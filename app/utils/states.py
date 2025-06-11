from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    """Состояния для FSM админ-панели"""
    # Добавление валютной пары
    add_pair_symbol = State()
    add_pair_threshold = State()

    # Редактирование валютной пары
    edit_threshold = State()

    # Настройки бота
    set_group_id = State()
    set_check_interval = State()
    set_default_threshold = State()