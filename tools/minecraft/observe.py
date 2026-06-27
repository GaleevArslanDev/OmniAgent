from tool import Tool

class ObserveTool(Tool):
    name = "observe"
    description = "Получить текущее наблюдение агента."
    args_schema = {}

    def use(self, client, arguments) -> tuple[bool, dict]:
        return True, client.observe()