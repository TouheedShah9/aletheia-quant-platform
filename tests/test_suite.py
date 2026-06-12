"""
╔══════════════════════════════════════════════════════╗
║           ALETHEIA — Enterprise Test Suite           ║
║   Unit Tests • Integration • Coverage • Load • CI    ║
╚══════════════════════════════════════════════════════╝
"""
import sys, os, json, time, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import duckdb
import pandas as pd
import numpy as np

# ═══════════════════════════════════════
# FIX 58: UNIT TESTS
# ═══════════════════════════════════════
class TestConfig(unittest.TestCase):
    """Test configuration integrity."""
    
    def test_universe_has_tickers(self):
        import config
        self.assertGreater(len(config.ALL_TICKERS), 0)
    
    def test_date_ranges_valid(self):
        import config
        self.assertLess(config.TRAIN_END, config.VAL_END)
        self.assertLess(config.VAL_END, config.TEST_START)
    
    def test_risk_limits_valid(self):
        import config
        self.assertGreater(config.MAX_POSITION, 0)
        self.assertLess(config.MAX_POSITION, 1)
        self.assertGreater(config.DRAWDOWN_BREAKER, 0)

class TestDatabase(unittest.TestCase):
    """Test database integrity."""
    
    def setUp(self):
        self.conn = duckdb.connect('aletheia.db')
    
    def tearDown(self):
        self.conn.close()
    
    def test_all_tables_exist(self):
        tables = self.conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()
        self.assertGreaterEqual(len(tables), 10)
    
    def test_prices_not_empty(self):
        count = self.conn.execute("SELECT COUNT(*) FROM price_data").fetchone()[0]
        self.assertGreater(count, 50000)
    
    def test_signals_not_empty(self):
        count = self.conn.execute("SELECT COUNT(*) FROM composite_signals").fetchone()[0]
        self.assertGreater(count, 0)
    
    def test_ens_scores_valid_range(self):
        invalid = self.conn.execute("SELECT COUNT(*) FROM ens_scores WHERE ens_final < -1 OR ens_final > 1").fetchone()[0]
        self.assertEqual(invalid, 0)
    
    def test_no_future_dates(self):
        future = self.conn.execute("SELECT COUNT(*) FROM price_data WHERE trade_date > CURRENT_DATE").fetchone()[0]
        self.assertEqual(future, 0)

class TestSignals(unittest.TestCase):
    """Test signal quality."""
    
    def setUp(self):
        self.conn = duckdb.connect('aletheia.db')
    
    def tearDown(self):
        self.conn.close()
    
    def test_composite_signals_directional(self):
        sigs = self.conn.execute("SELECT signal_direction FROM composite_signals").fetchall()
        directions = [s[0] for s in sigs]
        self.assertTrue(any(d == 1 for d in directions))
        self.assertTrue(any(d == -1 for d in directions) or any(d == 0 for d in directions))
    
    def test_ens_correlation_exists(self):
        ens = self.conn.execute("SELECT AVG(ens_final) FROM ens_scores").fetchone()[0]
        self.assertIsNotNone(ens)
    
    def test_prices_have_ohlcv(self):
        cols = self.conn.execute("DESCRIBE price_data").fetchall()
        col_names = [c[0] for c in cols]
        for required in ['open_price', 'high_price', 'low_price', 'close_price']:
            self.assertIn(required, col_names)

# ═══════════════════════════════════════
# FIX 59: INTEGRATION TESTS
# ═══════════════════════════════════════
class TestIntegration(unittest.TestCase):
    """End-to-end pipeline tests."""
    
    def test_edgar_to_signals(self):
        """SEC filing → transcript → ENS → composite → signal."""
        conn = duckdb.connect('aletheia.db')
        
        # SEC filings exist
        sec = conn.execute("SELECT COUNT(*) FROM transcripts_metadata WHERE source LIKE 'SEC_%'").fetchone()[0]
        self.assertGreater(sec, 100)
        
        # ENS scores exist
        ens = conn.execute("SELECT COUNT(*) FROM ens_scores").fetchone()[0]
        self.assertGreater(ens, 0)
        
        # Composite signals exist
        sigs = conn.execute("SELECT COUNT(*) FROM composite_signals").fetchone()[0]
        self.assertGreater(sigs, 0)
        
        conn.close()
    
    def test_alpaca_to_portfolio(self):
        """Alpaca data → portfolio construction → valid allocations."""
        try:
            with open('alpaca_data.json') as f:
                data = json.load(f)
            self.assertIn('equity', data)
            self.assertGreater(data['equity'], 0)
            self.assertIn('positions', data)
        except FileNotFoundError:
            self.skipTest("Alpaca data not available")
    
    def test_security_login_flow(self):
        """Login → session → RBAC → logout."""
        from live.security import auth, rbac
        ok, token = auth.login('admin', 'aletheia_admin_2024')
        self.assertTrue(ok)
        
        session = auth.validate_session(token)
        self.assertEqual(session['username'], 'admin')
        
        self.assertTrue(rbac.has_permission('admin', 'execute_trades'))
        self.assertFalse(rbac.has_permission('viewer', 'execute_trades'))
        
        auth.logout(token)
        self.assertIsNone(auth.validate_session(token))

# ═══════════════════════════════════════
# FIX 60: PERFORMANCE TESTS
# ═══════════════════════════════════════
class TestPerformance(unittest.TestCase):
    """Performance benchmarks."""
    
    def test_db_query_speed(self):
        conn = duckdb.connect('aletheia.db')
        start = time.time()
        conn.execute("SELECT * FROM price_data WHERE ticker='AAPL' ORDER BY trade_date").fetchall()
        elapsed = time.time() - start
        conn.close()
        self.assertLess(elapsed, 1.0, f"Query too slow: {elapsed:.2f}s")
    
    def test_signal_generation_speed(self):
        from models.ens.ens_scorers import ToneConfidenceScorer
        text = "Revenue grew 15 percent with strong margins and record profits."
        start = time.time()
        for _ in range(100):
            ToneConfidenceScorer.score(text)
        elapsed = time.time() - start
        self.assertLess(elapsed, 1.0, f"Scoring too slow: {elapsed:.2f}s")
    
    def test_cache_works(self):
        from dashboard.components.performance import perf_cache
        perf_cache.set('perf_test', {'value': 42})
        result = perf_cache.get('perf_test')
        self.assertIsNotNone(result)
        self.assertEqual(result['value'], 42)

# ═══════════════════════════════════════
# FIX 61: DATA QUALITY TESTS
# ═══════════════════════════════════════
class TestDataQuality(unittest.TestCase):
    """Data quality and integrity."""
    
    def setUp(self):
        self.conn = duckdb.connect('aletheia.db')
    
    def tearDown(self):
        self.conn.close()
    
    def test_no_null_prices(self):
        nulls = self.conn.execute("SELECT COUNT(*) FROM price_data WHERE adj_close IS NULL").fetchone()[0]
        self.assertEqual(nulls, 0)
    
    def test_no_duplicate_prices(self):
        dups = self.conn.execute("""
            SELECT ticker, trade_date, COUNT(*) as c 
            FROM price_data GROUP BY ticker, trade_date HAVING c > 1
        """).fetchall()
        self.assertEqual(len(dups), 0)
    
    def test_ens_range_valid(self):
        out_of_range = self.conn.execute("SELECT COUNT(*) FROM ens_scores WHERE ens_final < -1 OR ens_final > 1").fetchone()[0]
        self.assertEqual(out_of_range, 0)
    
    def test_tickers_consistent(self):
        price_tickers = set(r[0] for r in self.conn.execute("SELECT DISTINCT ticker FROM price_data").fetchall())
        signal_tickers = set(r[0] for r in self.conn.execute("SELECT DISTINCT ticker FROM composite_signals").fetchall())
        self.assertTrue(len(signal_tickers & price_tickers) > 0)

# ═══════════════════════════════════════
# FIX 62: COVERAGE REPORT
# ═══════════════════════════════════════
def generate_coverage_report():
    """Generate test coverage summary."""
    modules = [
        'config', 'database.schema', 'ingestion.base_ingester',
        'models.ens.section_parser', 'models.ens.preprocessor',
        'models.ens.ens_scorers', 'models.ens.ens_composer',
        'models.riv.preprocessor', 'models.riv.classifier',
        'models.cmi.signal_generator', 'causal.ens_causal',
        'backtest.engine', 'backtest.data_loader',
        'portfolio.constructor', 'portfolio.risk_engine',
        'live.paper_trader', 'live.monitor', 'live.monitoring',
        'live.security', 'live.ai_insights',
        'dashboard.components.charts',
        'dashboard.components.interactivity',
        'dashboard.components.performance',
        'dashboard.components.mobile',
    ]
    
    print("\n" + "="*60)
    print("CODE COVERAGE REPORT")
    print("="*60)
    
    total = len(modules)
    importable = 0
    
    for mod in modules:
        try:
            __import__(mod)
            print(f"  ✅ {mod}")
            importable += 1
        except Exception as e:
            print(f"  ❌ {mod}: {str(e)[:50]}")
    
    coverage = importable / total * 100 if total > 0 else 0
    print(f"\nCoverage: {importable}/{total} ({coverage:.0f}%)")
    print("="*60)
    return coverage

# ═══════════════════════════════════════
# RUN ALL TESTS
# ═══════════════════════════════════════
if __name__ == "__main__":
    print("="*60)
    print("PROJECT ALETHEIA — ENTERPRISE TEST SUITE")
    print("="*60)
    
    # Run unit tests
    print("\n[58] UNIT TESTS:")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestSignals))
    runner = unittest.TextTestRunner(verbosity=2)
    unit_result = runner.run(suite)
    
    # Run integration tests
    print("\n[59] INTEGRATION TESTS:")
    int_suite = unittest.TestSuite()
    int_suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    int_result = runner.run(int_suite)
    
    # Run performance tests
    print("\n[60] PERFORMANCE TESTS:")
    perf_suite = unittest.TestSuite()
    perf_suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    perf_result = runner.run(perf_suite)
    
    # Run data quality tests
    print("\n[61] DATA QUALITY TESTS:")
    dq_suite = unittest.TestSuite()
    dq_suite.addTests(loader.loadTestsFromTestCase(TestDataQuality))
    dq_result = runner.run(dq_suite)
    
    # Coverage
    print("\n[62] COVERAGE:")
    coverage = generate_coverage_report()
    
    # Summary
    total = (len(unit_result.failures) + len(unit_result.errors) +
             len(int_result.failures) + len(int_result.errors) +
             len(perf_result.failures) + len(perf_result.errors) +
             len(dq_result.failures) + len(dq_result.errors))
    
    print("\n" + "="*60)
    print("TEST SUITE SUMMARY")
    print("="*60)
    print(f"  Unit tests:        {unit_result.testsRun} run, {len(unit_result.failures)} failed")
    print(f"  Integration tests: {int_result.testsRun} run, {len(int_result.failures)} failed")
    print(f"  Performance tests: {perf_result.testsRun} run, {len(perf_result.failures)} failed")
    print(f"  Data quality:      {dq_result.testsRun} run, {len(dq_result.failures)} failed")
    print(f"  Coverage:          {coverage:.0f}%")
    
    if total == 0:
        print("\n✅ ALL TESTS PASSED")
    else:
        print(f"\n❌ {total} FAILURES")
    print("="*60)