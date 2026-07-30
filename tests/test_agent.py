import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import DataAnalystAgent
from logger import JSONLLogger

async def test_highest_mmr():
    """Test the maternal mortality question."""
    logger = JSONLLogger("test_logs", "test_mmr")
    await logger.__aenter__()
    
    agent = DataAnalystAgent(logger)
    
    question = 'Which state has the highest maternal mortality rate based on MOSPI data? Reply with ONLY this JSON object and nothing else: {"state": "<state name>"}'
    
    print(f"Question: {question}")
    answer = await agent.analyze(question)
    print(f"Answer: {json.dumps(answer, indent=2)}")
    
    print(f"\nLog file: {logger.get_log_path()}")
    
    await logger.__aexit__(None, None, None)

async def test_forecast():
    """Test the forecast question."""
    logger = JSONLLogger("test_logs", "test_forecast")
    await logger.__aenter__()
    
    agent = DataAnalystAgent(logger)
    
    question = 'Forecast flow rate for these inputs: [10.5, 20.3, 30.1, 40.7, 50.2]. Reply with ONLY {"values": [<numbers>]}'
    
    print(f"Question: {question}")
    answer = await agent.analyze(question)
    print(f"Answer: {json.dumps(answer, indent=2)}")
    
    print(f"\nLog file: {logger.get_log_path()}")
    
    await logger.__aexit__(None, None, None)

async def test_model_build():
    """Test the model build question."""
    logger = JSONLLogger("test_logs", "test_model")
    await logger.__aenter__()
    
    agent = DataAnalystAgent(logger)
    
    question = 'Build a model to forecast flow rate. Reply with ONLY {"status": "<status>"}'
    
    print(f"Question: {question}")
    answer = await agent.analyze(question)
    print(f"Answer: {json.dumps(answer, indent=2)}")
    
    print(f"\nLog file: {logger.get_log_path()}")
    
    await logger.__aexit__(None, None, None)

async def main():
    print("=" * 60)
    print("TEST 1: Highest Maternal Mortality Rate")
    print("=" * 60)
    await test_highest_mmr()
    
    print("\n" + "=" * 60)
    print("TEST 2: Forecast")
    print("=" * 60)
    await test_forecast()
    
    print("\n" + "=" * 60)
    print("TEST 3: Model Build")
    print("=" * 60)
    await test_model_build()
    
    # Show log files
    print("\n" + "=" * 60)
    print("LOG FILES (JSONL format - one JSON per line)")
    print("=" * 60)
    
    import glob
    for log_file in glob.glob("test_logs/*.jsonl"):
        print(f"\n--- {log_file} ---")
        with open(log_file) as f:
            for line in f:
                print(line.strip())

if __name__ == "__main__":
    asyncio.run(main())