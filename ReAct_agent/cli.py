from __future__ import annotations

import argparse
import time

from intelligent_agent import IntelligentAgent


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="智能监控系统 Agent CLI")
    parser.add_argument("-q", "--question", help="单次提问内容")
    parser.add_argument("--token", help="可选，用户 token")
    parser.add_argument("--conversation", help="可选，会话 key")
    parser.add_argument("--verbose", action="store_true", help="显示 Agent 处理过程")
    return parser


def _event_logger(verbose: bool):
    def _log(stage: str, message: str) -> None:
        if not verbose:
            return
        now = time.strftime("%H:%M:%S")
        print(f"[{now}] {stage}: {message}")

    return _log


def run_cli() -> None:
    args = _build_parser().parse_args()
    agent = IntelligentAgent()
    event_logger = _event_logger(args.verbose)

    if args.question:
        event_logger("start", "received one-shot question")
        answer = agent.process_question(
            args.question,
            on_event=event_logger,
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
                on_event=event_logger,
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
