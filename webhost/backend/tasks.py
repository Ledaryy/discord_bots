#
# Author: Andrew Kulishov <support@andrewkulishov.com>
# Copyright (C) 2022 Andrew Kulishov - All Rights Reserved
#
# Created on Sun May 29 2022
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
#
# If there are any issues contact me on the email above.
#


import logging
import random
from datetime import datetime, timedelta, timezone
from time import sleep

import celery
from celery import shared_task

from .bots.collecter import BotCacheManager, BotTools
from .models import ErrorLog
from .models.bots import Bot, BotRoles
from .settings import WORK_CHANNEL_ID

logger = logging.getLogger(__name__)


@shared_task
def start_bot(bot_id, delay):
    logger.info(f"Started background task, init start bot: {bot_id}, delay: {delay}")
    try:

        eta = datetime.now() + timedelta(minutes=delay)

        celery.current_app.send_task(
            name="backend.tasks._start_bot",
            kwargs={
                "bot_id": bot_id,
            },
            eta=eta,
        )

    except Exception as e:
        logger.error(f"Error {e} while starting bot {bot_id}")
    logger.info(f"Finished background init start bot for bot: {bot_id}")


@shared_task()
def _start_bot(bot_id: int):

    logger.info(f"Started background start bot for bot: {bot_id}")

    bot = Bot.objects.get(id=bot_id)
    bot.is_active = True
    bot.save()

    if bot.role == BotRoles.disabled:
        logger.info(f"This bot is disabled: {bot}")

    if bot.role == BotRoles.collecter:
        bot.task_schedule.start_all()

    logger.info(f"Finished background start bot task for bot: {bot_id}")


@shared_task()
def send_message(bot_id: int, message: str, delay: int):
    logger.info(f"Started background send message for bot: {bot_id}")

    eta = datetime.now() + timedelta(minutes=delay)

    celery.current_app.send_task(
        name="backend.tasks._send_message",
        kwargs={
            "bot_id": bot_id,
            "message": message,
        },
        eta=eta,
    )

    logger.info(f"Finished background send message for bot: {bot_id}")


@shared_task()
def _send_message(bot_id: int, message: str):
    logger.info(f"Started background send message for bot: {bot_id}")

    bot = Bot.objects.get(id=bot_id)
    _bot = BotTools(bot)

    success, error = _bot.send_message(WORK_CHANNEL_ID, message)

    if not success:
        logger.error(f"Error while sending message: {error}")
        error_log = ErrorLog(owner=bot, comment="Error while sending message to the chat", body=error)
        error_log.save()

    logger.info(f"Finished background send message for bot: {bot_id}")


@shared_task()
def execute_tasks(bot_id: int, tasks_list: list):
    logger.info(f"Started background execute task for bot: {bot_id}, tasks: {tasks_list}")

    bot = Bot.objects.get(id=bot_id)

    if bot.is_active:
        bot_collecter = BotTools(bot)
        cache_manager = BotCacheManager(bot)

        if cache_manager.is_reserved:
            while cache_manager.is_reserved:
                logger.info(f"Chat is reserved, Bot {bot} with task {tasks_list} is on hold, waiting...")
                delay_seconds = round(random.uniform(3, 15), 5)
                sleep(delay_seconds)
                cache_manager.refresh_cache()
            else:
                logger.info(f"Chat is free, Bot {bot} with task {tasks_list} is ready to work")
                cache_manager.reserve(tasks_list)
        else:
            cache_manager.reserve(tasks_list)

        if "work" in tasks_list:
            bot_collecter.collect_work()

        if "collect" in tasks_list:
            bot_collecter.collect_collect_daily()

        if "crime" in tasks_list:
            bot_collecter.collect_crime()

        cache_manager.release()

    else:
        logger.info(f"Bot is not active, task execution skipped: {bot}")

    logger.info(f"Finished background execute task for bot: {bot_id}")


@shared_task
def stop_bot(bot_id, delay):
    logger.info(f"Started initial background stop task for bot: {bot_id}, delay: {delay}")

    eta = datetime.now() + timedelta(minutes=delay)

    celery.current_app.send_task(
        name="backend.tasks._stop_bot",
        kwargs={
            "bot_id": bot_id,
        },
        eta=eta,
    )

    logger.info(f"Finished initial background stop task for bot: {bot_id}")


@shared_task
def _stop_bot(bot_id):
    logger.info(f"Started background stop task for bot: {bot_id}")

    bot = Bot.objects.get(id=bot_id)
    bot.is_active = False
    bot.save()

    logger.info(f"Finished background stop task for bot: {bot_id}")


@shared_task
def schedule_tasks():
    logger.info("Started background schedule tasks")

    bots = Bot.objects.all()

    for bot in bots:

        if bot.is_active:

            if bot.role == BotRoles.collecter:

                diff = bot.task_schedule.next_work_task - datetime.now(timezone.utc)
                if diff < timedelta(minutes=2):
                    celery.current_app.send_task(
                        name="backend.tasks.execute_tasks",
                        kwargs={
                            "bot_id": bot.id,
                            "tasks_list": ["work"],
                        },
                        eta=bot.task_schedule.next_work_task,
                    )
                    bot.task_schedule.reschedule_work()

                diff = bot.task_schedule.next_crime_task - datetime.now(timezone.utc)
                if diff < timedelta(minutes=2):
                    celery.current_app.send_task(
                        name="backend.tasks.execute_tasks",
                        kwargs={
                            "bot_id": bot.id,
                            "tasks_list": ["crime"],
                        },
                        eta=bot.task_schedule.next_crime_task,
                    )
                    bot.task_schedule.reschedule_crime()

                diff = bot.task_schedule.next_collect_task - datetime.now(timezone.utc)
                if diff < timedelta(minutes=2):
                    celery.current_app.send_task(
                        name="backend.tasks.execute_tasks",
                        kwargs={
                            "bot_id": bot.id,
                            "tasks_list": ["collect"],
                        },
                        eta=bot.task_schedule.next_collect_task,
                    )
                    bot.task_schedule.rechedule_collect()

    logger.info("Finished background schedule tasks")


@shared_task
def transaction(bot_id, value, transaction_type, receiver=None):
    logger.info(f"Started background send money for bot: {bot_id}")

    bot = Bot.objects.get(id=bot_id)
    bot_tools = BotTools(bot)

    cache_manager = BotCacheManager(bot)

    if cache_manager.is_reserved:
        while cache_manager.is_reserved:
            logger.info(f"Chat is reserved, Bot {bot} with task {transaction_type} is on hold, waiting...")
            delay_seconds = round(random.uniform(3, 15), 5)
            sleep(delay_seconds)
            cache_manager.refresh_cache()
        else:
            logger.info(f"Chat is free, Bot {bot} with task {transaction_type} is ready to work")
            cache_manager.reserve(transaction_type)
    else:
        cache_manager.reserve(transaction_type)

    if transaction_type == "withdraw":
        success, error = bot_tools.send_message(WORK_CHANNEL_ID, f",with {value}")
    if transaction_type == "deposit":
        success, error = bot_tools.send_message(WORK_CHANNEL_ID, f",dep {value}")
    if transaction_type == "send":
        success, error = bot_tools.send_message(WORK_CHANNEL_ID, f",give <@{receiver}> {value}")

    cache_manager.release()

    if not success:
        logger.error(f"Error while sending message: {error}")
        error_log = ErrorLog(
            owner=bot, comment=f"Error while sending {transaction_type} message to the chat", body=error
        )
        error_log.save()

    logger.info(f"Finished background send money for bot: {bot_id}")
