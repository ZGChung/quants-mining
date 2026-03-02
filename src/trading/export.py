"""
结果导出模块
"""

import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ResultExporter:
    """结果导出器"""
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_backtest_result(
        self,
        result: Dict,
        strategy_name: str,
        tickers: List[str],
        filename: Optional[str] = None
    ) -> str:
        """
        导出回测结果
        
        Args:
            result: 回测结果字典
            strategy_name: 策略名称
            tickers: 股票列表
            filename: 文件名（可选）
            
        Returns:
            导出文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_{strategy_name}_{timestamp}"
        
        # 导出为 CSV
        equity_curve = result.get('equity_curve')
        if equity_curve is not None:
            csv_path = self.output_dir / f"{filename}.csv"
            equity_curve.to_csv(csv_path)
            logger.info(f"Exported equity curve to {csv_path}")
        
        # 导出为 JSON (包含指标)
        json_data = {
            'strategy': strategy_name,
            'tickers': tickers,
            'metrics': {
                'total_return': result.get('total_return'),
                'annual_return': result.get('annual_return'),
                'sharpe_ratio': result.get('sharpe_ratio'),
                'max_drawdown': result.get('max_drawdown'),
                'total_trades': result.get('total_trades'),
                'win_rate': result.get('win_rate'),
            },
            'timestamp': datetime.now().isoformat()
        }
        
        json_path = self.output_dir / f"{filename}.json"
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        logger.info(f"Exported metrics to {json_path}")
        
        return str(csv_path)
    
    def export_optimization_result(
        self,
        optimization_result,
        strategy_name: str,
        filename: Optional[str] = None
    ) -> str:
        """
        导出优化结果
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"optimization_{strategy_name}_{timestamp}"
        
        # 导出所有结果为 CSV
        results_data = []
        for r in optimization_result.all_results:
            row = r['params'].copy()
            row['total_return'] = r['total_return']
            row['sharpe_ratio'] = r['sharpe_ratio']
            row['max_drawdown'] = r['max_drawdown']
            row['total_trades'] = r['total_trades']
            results_data.append(row)
        
        df = pd.DataFrame(results_data)
        csv_path = self.output_dir / f"{filename}.csv"
        df.to_csv(csv_path, index=False)
        
        logger.info(f"Exported optimization results to {csv_path}")
        
        # 导出最佳参数为 JSON
        best_params = {
            'strategy': strategy_name,
            'best_params': optimization_result.best_params,
            'best_sharpe': optimization_result.best_sharpe,
            'best_return': optimization_result.best_return,
            'timestamp': datetime.now().isoformat()
        }
        
        json_path = self.output_dir / f"{filename}_best.json"
        with open(json_path, 'w') as f:
            json.dump(best_params, f, indent=2)
        
        return str(csv_path)
    
    def export_trades(
        self,
        trades: List,
        filename: Optional[str] = None
    ) -> str:
        """
        导出交易记录
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trades_{timestamp}"
        
        trades_data = []
        for t in trades:
            trades_data.append({
                'date': t.date if hasattr(t, 'date') else t.entry_date,
                'ticker': t.ticker,
                'action': t.action if hasattr(t, 'action') else ('BUY' if t.quantity > 0 else 'SELL'),
                'quantity': abs(t.quantity),
                'price': t.price,
                'value': t.value if hasattr(t, 'value') else t.quantity * t.price,
                'commission': t.commission if hasattr(t, 'commission') else 0,
            })
        
        df = pd.DataFrame(trades_data)
        csv_path = self.output_dir / f"{filename}.csv"
        df.to_csv(csv_path, index=False)
        
        logger.info(f"Exported {len(trades)} trades to {csv_path}")
        
        return str(csv_path)
    
    def create_report(
        self,
        results: Dict[str, Dict],
        filename: str = "strategy_comparison"
    ) -> str:
        """
        创建策略对比报告
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename}_{timestamp}"
        
        # 创建汇总表
        summary_data = []
        for strategy_name, result in results.items():
            summary_data.append({
                'strategy': strategy_name,
                'total_return': result.get('total_return', 0),
                'annual_return': result.get('annual_return', 0),
                'sharpe_ratio': result.get('sharpe_ratio', 0),
                'max_drawdown': result.get('max_drawdown', 0),
                'total_trades': result.get('total_trades', 0),
            })
        
        df = pd.DataFrame(summary_data)
        df = df.sort_values('sharpe_ratio', ascending=False)
        
        csv_path = self.output_dir / f"{filename}.csv"
        df.to_csv(csv_path, index=False)
        
        logger.info(f"Created strategy comparison report: {csv_path}")
        
        return str(csv_path)


if __name__ == "__main__":
    # 测试
    from src.data.mock import generate_multiple_stocks
    from src.data import add_indicators
    from src.trading.strategies import create_strategy
    from src.trading.backtesting import PortfolioBacktester
    
    # 简单回测
    tickers = ['AAPL', 'MSFT']
    data = generate_multiple_stocks(tickers, start_date="2024-01-01")
    for ticker in data:
        data[ticker] = add_indicators(data[ticker])
    
    strategy = create_strategy('sma_crossover', fast_period=20, slow_period=50)
    backtester = PortfolioBacktester(initial_capital=100000)
    result = backtester.run(data, strategy)
    
    # 导出
    exporter = ResultExporter()
    exporter.export_backtest_result(result, 'sma_crossover', tickers)
    exporter.export_trades(result.get('trades', []))
    
    print("✅ Export test completed")
