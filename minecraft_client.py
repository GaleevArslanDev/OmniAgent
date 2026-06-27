import threading
from abc import ABC
from typing import Any

from javascript import require, On, Once, AsyncTask, once, off, terminate

from client_interface import ClientInterface


class MinecraftClient(ClientInterface, ABC):
    def __init__(self, name="Omni", host="localhost", port=3000, version="1.20.1", hide_errors=False):
        self.bot_params = {"username": name, "host": host, "port": port, "version": version, "hideErrors": hide_errors}
        self.mineflayer = require("mineflayer")
        self.bot = None
        self._start_bot()

    def _start_bot(self) -> None:
        self.bot = self.mineflayer.createBot(self.bot_params)
        self._start_events()

    def _start_events(self) -> None:
        @On(self.bot, "login")
        def login(*args):
            pass

        @On(self.bot, "messagestr")
        def messagestr(*args):
            # message = args[0]
            #
            # words = message.split(" ")
            # if len(words) > 1:
            #     message_no_tag = " ".join(words[1:])
            # else:
            #     message_no_tag = message
            pass

    def stop(self):
        if self.bot:
            self.bot.quit()  # Отключаем бота от сервера Minecraft
        terminate()

    def set_control_state_for(self, action: str, secs: float) -> None:
        """
        Надежный инструмент движения для агента.
        Считает тики напрямую через событие игры и жестко блокирует Python до остановки.
        """
        total_ticks = int(secs * 20)
        ticks_passed = 0

        # Создаем событие для блокировки текущего потока Python
        done = threading.Event()

        # Зажимаем клавишу движения
        self.bot.setControlState(action, True)

        # Нам нужно объявить функцию-обработчик заранее, чтобы потом её удалить
        def on_tick(*args):
            nonlocal ticks_passed
            ticks_passed += 1

            # Если отсчитали нужные тики
            if ticks_passed >= total_ticks:
                # 1. Гарантированно выключаем управление
                self.bot.clearControlStates()
                # 2. Отписываемся от события, чтобы не спамить память
                self.bot.removeListener("physicsTick", on_tick)
                # 3. Даем сигнал Python, что можно идти дальше
                done.set()

        # Подписываемся на каждый игровой тик напрямую через объект бота
        self.bot.on("physicsTick", on_tick)

        # Ждем здесь, пока on_tick не вызовет done.set()
        done.wait()


    def say(self, text: str) -> None:
        self.bot.chat(text)

    def execute(self, action: str, **kwargs) -> bool:
        pass

    def get_available_actions(self) -> list[str]:
        pass

    def observe(self) -> dict[str, Any]:
        pos = self.bot.entity.position
        return {
            "position": {
                "x": pos.x,
                "y": pos.y,
                "z": pos.z,
            },
            "health": self.bot.health,
            "food": self.bot.food,
        }

    def reset(self) -> bool:
        pass
