
import sys
import os
from pathlib import Path
import traceback

# 프로젝트 루트를 path에 추가
sys.path.append(str(Path(__file__).parent.parent))

from worker.automation.chatgpt_client import ChatGPTClient

def main():
    print("🚀 [TEST] 워크플로우 테스트 시작")
    
    test_story = "한 소년이 낡은 검을 주웠는데, 그 검은 사실 고대 왕국의 마지막 열쇠였다."
    
    try:
        with ChatGPTClient() as client:
            print(f"📝 입력 스토리: {test_story}")
            
            results = client.run_video_generation_workflow(test_story)
            
            print("\n✅ 워크플로우 테스트 성공!")
            print("="*40)
            print(f"📖 기승전결 (길이: {len(results['expanded_story'])})")
            print(f"🎬 스토리보드 (길이: {len(results['storyboard'])})")
            print(f"✨ 프롬프트 (길이: {len(results['prompts'])})")
            print("="*40)
            
            # 결과 일부 출력
            # print("--- Expanded Story ---\n", results['expanded_story'][:200])
            
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        
        with open("test_error_log.txt", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
            
        sys.exit(1)

if __name__ == "__main__":
    main()
