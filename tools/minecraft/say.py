from tool import Tool

class SayTool(Tool):
    name = "say"
    description = "Написать сообщение в чат Minecraft."
    args_schema = {
        "text": "string - текст сообщения"
    }

    def use(self, client, arguments) -> tuple[bool, None]:
        text = arguments["text"]
        client.say(text)
        return True, None