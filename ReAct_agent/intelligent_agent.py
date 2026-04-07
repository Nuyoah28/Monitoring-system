from __future__ import annotations

from agent_core.react_agent import ReactIntelligentAgent
from agent_core.utils import is_non_retryable_spark_error

IntelligentAgent = ReactIntelligentAgent

__all__ = [
    "IntelligentAgent",
    "ReactIntelligentAgent",
    "is_non_retryable_spark_error",
]


def main() -> None:
    print("=" * 60)
    print("智能监控系统 AI Agent")
    print("=" * 60)
    print("输入 exit 或 quit 退出。\n")

    agent = IntelligentAgent()
    print("Agent 初始化成功。")

    while True:
        try:
            question = input("\n请输入问题: ").strip()
            if not question:
                continue
            if question.lower() in {"exit", "quit"}:
                print("再见。")
                break
            answer = agent.process_question(question)
            print("\n" + "=" * 60)
            print(answer)
            print("=" * 60)
        except KeyboardInterrupt:
            print("\n再见。")
            break
        except Exception as exc:
            print(f"\n处理失败: {exc}")


if __name__ == "__main__":
    main()
