from __future__ import annotations

import argparse

from intelligent_agent import IntelligentAgent


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="智能监控系统 Agent CLI")
    parser.add_argument("-q", "--question", help="单次提问内容")
    parser.add_argument("--token", help="可选，用户 token")
    parser.add_argument("--conversation", help="可选，会话 key")
    return parser


def run_cli() -> None:
    args = _build_parser().parse_args()
    agent = IntelligentAgent()

    if args.question:
        answer = agent.process_question(
            args.question,
            user_token=args.token,
            conversation_key=args.conversation,
        )
        print(answer)
        return

    print("智能监控系统 AI Agent CLI")
    print("输入 exit 或 quit 退出。")
    while True:
        try:
            question = input("\n请输入问题: ").strip()
            if not question:
                continue
            if question.lower() in {"exit", "quit"}:
                print("再见。")
                break
            answer = agent.process_question(
                question,
                user_token=args.token,
                conversation_key=args.conversation,
            )
            print("\n" + answer)
        except KeyboardInterrupt:
            print("\n再见。")
            break
        except Exception as exc:
            print(f"处理失败: {exc}")


if __name__ == "__main__":
    run_cli()
