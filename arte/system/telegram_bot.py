import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


class TelegramBot:
    """
    Telegram bot 들이 공통적으로 사용하는 모듈
    """

    def __init__(self, name: str, token: str, id: int, start_message: str):
        """
        이름, 토큰, 채팅방 ID를 init
        """
        self.name = name
        self.updater = Updater(token)
        self.id = id
        self.start_message = start_message

    def sendMessage(self, text: str):
        """
        sendMessage 함수 wrapping
        """

        def add_message(context):
            job = context.job
            self.updater.dispatcher.bot.sendMessage(chat_id=self.id, text=job.context)

        self.updater.job_queue.run_once(add_message, 0, context=text)

    def stop(self):
        """
        kill bot
        """
        self.updater.start_polling()
        self.updater.dispatcher.stop()
        self.updater.job_queue.stop()
        self.updater.stop()

    def start(self):
        """
        Bot을 실행시킴
        handler가 추가 된 후에 start해야함
        """
        self.updater.start_polling()
        self.sendMessage(self.start_message)

    def add_handler(self, cmd: str, func, pass_args: bool):
        """
        add_handler wrapping
        cmd : 봇에 전달할 명령어
        func : 봇이 명령어를 전달받았을 때 실행 할 함수
        pass_args : 실행 할 함수에 인자를 전달해야 할 때 true
        """
        self.updater.dispatcher.add_handler(CommandHandler(cmd, func, pass_args=pass_args))


class DominicBot(TelegramBot):
    def __init__(self):
        """
        Simon information 추가해주기
        """
        name = "Dominic"
        token = ""
        id = 0
        start_message = "Arbi start!"
        TelegramBot.__init__(self, name, token, id, start_message)
        self.updater.stop()
        self.trader = None

    def bot_manager_setting(self):
        """
        bot add handler
        """
        if self.trader is not None:
            self.add_handler("except", self.add_except_list, pass_args=True)
            self.add_handler("cept", self.del_except_list, pass_args=True)
            self.add_handler("threshold", self.adjust_threshold, pass_args=True)
            self.start()

    def adjust_threshold(self, update, context):
        self.trader.strategy.premium_threshold = float(context.args[0])
        self.sendMessage("현재 알람 기준가 : " + str(self.trader.strategy.premium_threshold))

    def add_except_list(self, update, context):
        """
        runner라는 scheduler의 job을 pause
        """
        if context.args[0] not in self.trader.except_list:
            self.trader.except_list.append(context.args[0])
            self.sendMessage("현재 제외된 항목 : " + str(self.trader.except_list))

    def del_except_list(self, update, context):
        """
        runner라는 scheduler의 job을 resume
        """
        if context.args[0] in self.trader.except_list:
            self.trader.except_list.remove(context.args[0])
            self.sendMessage("현재 제외된 항목 : " + str(self.trader.except_list))


class SimonBot(TelegramBot):
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
        start_message = "Arte start!"
        TelegramBot.__init__(self, name, token, id, start_message)
        self.updater.stop()
        self.trader = None

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
