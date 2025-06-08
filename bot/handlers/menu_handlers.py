# from aiogram import Router, F
# from aiogram.types import Message
# from aiogram.fsm.context import FSMContext
#
# from bot.keyboards.main_menu import get_main_menu
#
# router = Router()
#
# @router.message(F.text == "📝 Мои заявки")
# async def show_applications(message: Message):
#     text = (
#         "📑 Ваши заявки:\n\n"
#         "У вас пока нет поданных заявок.\n"
#         "Для подачи заявки сначала пройдите подбор факультета."
#     )
#     await message.answer(text)
#
# @router.message(F.text == "👤 Профиль")
# async def show_profile(message: Message):
#     user = message.from_user
#     text = (
#         f"👤 Ваш профиль:\n\n"
#         f"Имя: {user.first_name}\n"
#         f"Username: @{user.username or 'не указан'}\n"
#         f"ID: {user.id}\n\n"
#         "Для редактирования профиля обратитесь к администратору."
#     )
#     await message.answer(text)
#
# @router.message(F.text == "ℹ️ Помощь")
# async def show_help(message: Message):
#     text = (
#         "🤖 Справка по использованию бота:\n\n"
#         "🎓 Подобрать факультет - пройти анкету для получения рекомендации\n"
#         "📝 Мои заявки - посмотреть поданные заявки\n"
#         "👤 Профиль - информация о вашем аккаунте\n"
#         "ℹ️ Помощь - эта справка\n\n"
#         "Для отмены любого действия используйте команду /start\n\n"
#         "По техническим вопросам обращайтесь: @admin_tusur"
#     )
#     await message.answer(text)
#
# @router.message(F.text.in_(["❌ Отменить анкету", "🏠 Главное меню"]))
# async def cancel_action(message: Message, state: FSMContext):
#     await state.clear()
#     await message.answer(
#         "Действие отменено. Возвращаемся в главное меню.",
#         reply_markup=get_main_menu()
#     )
