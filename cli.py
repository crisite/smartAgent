
from services.chat_service import ModelCallError, create_chat_service


def main():
    service = create_chat_service()
    while True:
        try:
            question = input("请输入问题，输入 quit 退出：").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if question.lower() == "quit":
            break

        try:
            result = service.ask(question)
        except (ValueError, ModelCallError) as error:
            print(error)
            continue

        print(result["answer"])
        usage = result["usage"]
        if usage is None:
            print("本次调用未返回 token 用量信息")
        else:
            print(
                f"token 用量：输入 {usage['input_tokens']}，"
                f"输出 {usage['output_tokens']}，总计 {usage['total_tokens']}"
            )

if __name__ == '__main__':
    main()
