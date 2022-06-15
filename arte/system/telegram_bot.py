import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


class TelegramBot:
    """
    Telegram bot 들이 공통적으로 사용하는 모듈
    """

    def __init__(self, name: str, token: str, id: int):
        """
        이름, 토큰, 채팅방 ID를 init
        """
        self.name = name
        self.core = telegram.Bot(token)
        self.updater = Updater(token)
        self.id = id

    def sendMessage(self, text: str):
        """
        sendMessage 함수 wrapping
        """
        self.core.sendMessage(chat_id=self.id, text=text)

    def stop(self):
        """
        kill bot
        """
        self.updater.start_polling()
        self.updater.dispatcher.stop()
        self.updater.job_queue.stop()
        self.updater.stop()


class SimonManager(TelegramBot):
    """
    하나의 봇(Simon)을 관리하기 위한 매니저
    """

    def __init__(self):
        """
        Simon information 추가해주기
        """
        name = "Simon"
        token = ""
        id = 0
        TelegramBot.__init__(self, name, token, id)
        self.updater.stop()
        self.trader = None

    def add_handler(self, cmd: str, func, pass_args: bool):
        """
        add_handler wrapping
        cmd : 봇에 전달할 명령어
        func : 봇이 명령어를 전달받았을 때 실행 할 함수
        pass_args : 실행 할 함수에 인자를 전달해야 할 때 true
        """
        self.updater.dispatcher.add_handler(
            CommandHandler(cmd, func, pass_args=pass_args)
        )

    def start(self):
        """
        Bot을 실행시킴
        handler가 추가 된 후에 start해야함
        """
        self.sendMessage("Arte Start!")
        self.updater.start_polling()
        self.updater.idle()

    def bot_manager_setting(self):
        """
        bot add handler
        """
        if self.trader is not None:
            self.add_handler("pause", self.pause, pass_args=False)
            self.add_handler("resume", self.resume, pass_args=False)
            self.start()

    def pause(self, bot, update):
        """
        runner라는 scheduler의 job을 pause
        """
        self.trader.runner.pause()

    def resume(self, bot, update):
        """
        runner라는 scheduler의 job을 resume
        """
        self.trader.runner.resume()


if __name__ == "__main__":
    bot = SimonManager()
