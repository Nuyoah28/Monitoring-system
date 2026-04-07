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
    stage_label_map = {
        "start": "启动",
        "reading": "读取问题",
        "searching_skills": "搜索 skills",
        "planning": "规划调用",
        "using_tools": "使用工具",
        "thinking": "模型思考",
        "done": "完成",
    }

    def _log(stage: str, message: str) -> None:
        if not verbose:
            return
        now = time.strftime("%H:%M:%S")
        label = stage_label_map.get(stage, stage)
        print(f"[{now}] {label}: {message}")

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
    if not args.verbose:
        print("提示：加 --verbose 可显示运行状态（搜索skills、使用工具、模型思考等）。")
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
