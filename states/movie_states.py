from aiogram.fsm.state import StatesGroup, State

class AddMovie(StatesGroup):
    waiting_for_video = State()
    waiting_for_details = State() # Kod va Nom uchun