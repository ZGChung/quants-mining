"""
定时任务调度器
用于自动运行 QuantMining 任务
"""

import schedule
import time
import logging
from datetime import datetime
from pathlib import Path
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
    def log_task(self, task_name: str, message: str):
        """记录任务日志"""
        log_file = self.log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {task_name}: {message}\n"
        
        with open(log_file, "a") as f:
            f.write(log_entry)
        
        logger.info(f"{task_name}: {message}")
    
    def run_heartbeat(self):
        """运行心跳检查"""
        self.log_task("HEARTBEAT", "Starting heartbeat check...")
        
        try:
            from src.heartbeat import Heartbeat
            
            heartbeat = Heartbeat()
            status = heartbeat.check_health()
            
            self.log_task("HEARTBEAT", f"Status: {status.status}, Message: {status.message}")
            
            # 运行诊断
            report = heartbeat.run_diagnostics()
            for rec in report['recommendations']:
                self.log_task("HEARTBEAT", f"Recommendation: {rec}")
                
        except Exception as e:
            self.log_task("HEARTBEAT", f"Error: {e}")
    
    def run_optimization(self):
        """运行自动优化"""
        self.log_task("OPTIMIZATION", "Starting parameter optimization...")
        
        try:
            from src.data.mock import generate_multiple_stocks
            from src.data import add_indicators
            from src.trading.optimize import StrategyOptimizer
            
            tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
            data = generate_multiple_stocks(tickers, start_date="2024-01-01")
            for ticker in data:
                data[ticker] = add_indicators(data[ticker])
            
            param_grid = {
                'fast_period': [10, 20, 30],
                'slow_period': [30, 50, 70],
            }
            
            optimizer = StrategyOptimizer(data, 'sma_crossover', metric='sharpe_ratio')
            result = optimizer.optimize(param_grid)
            
            self.log_task("OPTIMIZATION", f"Best params: {result.best_params}")
            self.log_task("OPTIMIZATION", f"Best Sharpe: {result.best_sharpe:.3f}")
            
            # 保存结果
            result_file = self.log_dir / "optimization_results.json"
            with open(result_file, "w") as f:
                json.dump({
                    'best_params': result.best_params,
                    'best_sharpe': result.best_sharpe,
                    'best_return': result.best_return,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
                
        except Exception as e:
            self.log_task("OPTIMIZATION", f"Error: {e}")
    
    def run_daily_backtest(self):
        """运行每日回测"""
        self.log_task("DAILY_BACKTEST", "Running daily backtest...")
        
        try:
            from src.data.mock import generate_multiple_stocks
            from src.data import add_indicators
            from src.trading.strategies import create_strategy
            from src.trading.backtesting import PortfolioBacktester
            
            tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
            data = generate_multiple_stocks(tickers, start_date="2024-01-01")
            for ticker in data:
                data[ticker] = add_indicators(data[ticker])
            
            strategy = create_strategy('sma_crossover', fast_period=20, slow_period=50)
            backtester = PortfolioBacktester(initial_capital=100000, max_positions=3)
            result = backtester.run(data, strategy)
            
            self.log_task("DAILY_BACKTEST", f"Return: {result['total_return']:.2%}")
            self.log_task("DAILY_BACKTEST", f"Sharpe: {result['sharpe_ratio']:.2f}")
            
        except Exception as e:
            self.log_task("DAILY_BACKTEST", f"Error: {e}")
    
    def schedule_tasks(self):
        """设置定时任务"""
        # 每天早上 8 点运行心跳检查
        schedule.every().day.at("08:00").do(self.run_heartbeat)
        
        # 每天晚上 10 点运行优化
        schedule.every().day.at("22:00").do(self.run_optimization)
        
        # 每小时运行心跳检查
        schedule.every().hour.do(self.run_heartbeat)
        
        logger.info("Tasks scheduled successfully")
    
    def run(self):
        """运行调度器"""
        self.schedule_tasks()
        
        logger.info("Scheduler started. Press Ctrl+C to stop.")
        
        while True:
            schedule.run_pending()
            time.sleep(60)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="QuantMining Task Scheduler")
    parser.add_argument("--heartbeat", action="store_true", help="Run heartbeat check")
    parser.add_argument("--optimize", action="store_true", help="Run optimization")
    parser.add_argument("--backtest", action="store_true", help="Run daily backtest")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    scheduler = TaskScheduler()
    
    if args.heartbeat:
        scheduler.run_heartbeat()
    elif args.optimize:
        scheduler.run_optimization()
    elif args.backtest:
        scheduler.run_daily_backtest()
    elif args.daemon:
        scheduler.run()
    else:
        # 运行所有任务一次
        scheduler.run_heartbeat()
        scheduler.run_optimization()
        scheduler.run_daily_backtest()


if __name__ == "__main__":
    main()
