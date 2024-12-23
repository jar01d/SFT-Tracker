
import logging
import sqlite3
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler, filters
)

# from db.helper import check_cadet_exists, insert_cadet, insert_group, insert_srt_info, get_activities, get_status_id, get_cadet_id_by_tele_id, get_activity_id_by_activity_name

# Database connection
DATABASE_URL = "db/srt.db"
CUTOFF_TIME = 21  #12am

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def check_cadet_exists(tele_id):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM cadet WHERE telegram_id = ?", (tele_id,))
        result = cursor.fetchone()
        conn.close()
        return result  # Returns name if exists, None otherwise
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None


def insert_cadet(telegram_id, username, name):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Insert user data into the cadet table
        cursor.execute(
            """
            INSERT INTO cadet (telegram_id, telegram_username, name)
            VALUES (?, ?, ?)
            """,
            (telegram_id, username, name),
        )

        conn.commit()
        conn.close()
        return True

    except sqlite3.IntegrityError as e:
        print(f"Database error: {e}")
        return False


def get_activities():
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT activity_id, name FROM activity")
        activities = cursor.fetchall()
        conn.close()
        return activities
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []


# Helper function to insert SRT Info into the database
def insert_srt_info(cadet_id, activity_id, datetime_in, datetime_out, created_on, status_id):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO srt_info (cadet_id, activity_id, datetime_in, datetime_out, created_on, status_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (cadet_id, activity_id, datetime_in,
             datetime_out, created_on, status_id),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False


# Helper function to fetch the 'Ongoing' status ID
def get_status_id(status_name="Ongoing"):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status_id FROM status WHERE name = ?", (status_name,))
        status_id = cursor.fetchone()
        conn.close()
        return status_id[0] if status_id else None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None


def get_cadet_id_by_tele_id(telegram_id):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT cadet_id FROM cadet WHERE telegram_id = ?", (telegram_id,))
        status_id = cursor.fetchone()
        conn.close()
        return status_id[0] if status_id else None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None


def get_activity_id_by_activity_name(name):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT activity_id FROM activity WHERE name = ?", (name,))
        status_id = cursor.fetchone()
        conn.close()
        return status_id[0] if status_id else None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None


DATABASE_URL = "db/srt.db"


def get_srt_info(telegram_id):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()

        query = """
        SELECT 
            cadet.name AS cadet_name,
            activity.name AS activity_name,
            STRFTIME('%H%M', srt_info.datetime_in),
            STRFTIME('%H%M', srt_info.datetime_out),
            status.name AS status_name
        FROM 
            srt_info
        JOIN cadet ON srt_info.cadet_id = cadet.cadet_id
        JOIN activity ON srt_info.activity_id = activity.activity_id
        JOIN status ON srt_info.status_id = status.status_id
        WHERE cadet.telegram_id = ?
        ORDER BY srt_info.created_on DESC
        LIMIT 1
        """
        cursor.execute(query, (telegram_id, ))
        rows = cursor.fetchall()

        # Format the results
        formatted_results = []
        for row in rows:
            cadet_name, activity_name, datetime_in, datetime_out, status_name = row
            if not datetime_in and not datetime_out:
                formatted_results.append(
                    f"{cadet_name} | {activity_name} | {status_name}")
            elif not datetime_out:
                formatted_results.append(
                    f"{cadet_name} | {activity_name} | Started at {datetime_in} | {status_name}")
            else:
                formatted_results.append(
                    f"{cadet_name} | {activity_name} | Started at {datetime_in} | {datetime_out} | {status_name}")

        conn.close()
        return formatted_results[::-1][0]

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []


def has_srt_record_today(telegram_id):
    """
    Check if there is a record in the srt_info table for today for a specific cadet.

    Args:
        telegram_id (int): Telegram ID of the cadet.

    Returns:
        bool: True if a record exists for today, False otherwise.
    """
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()

        query = """
        SELECT date(created_on)
        FROM srt_info
        JOIN cadet ON srt_info.cadet_id = cadet.cadet_id
        WHERE cadet.telegram_id = ? AND date(created_on) = date('now')
        LIMIT 1
        """
        cursor.execute(query, (telegram_id,))

        result = cursor.fetchall()

        conn.close()
        if result:
            return True
        else:
            return False
        # return True
        # else:
        #     return False
        # return result is not None

    except sqlite3.Error as e:
        print(f"Database error for has_srt: {e}")
        return False


def srt_check_in(datetime_in, status_id, cadet_id):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Update query
        cursor.execute(
            """
            UPDATE srt_info
            SET datetime_in = ?, status_id = ?
            WHERE cadet_id = ?
            """,
            (datetime_in, status_id, cadet_id),
        )

        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False


def srt_check_out(datetime_out, status_id, cadet_id):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Update query
        cursor.execute(
            """
            UPDATE srt_info
            SET datetime_in = ?, status_id = ?
            WHERE cadet_id = ?
            """,
            (datetime_out, status_id, cadet_id),
        )

        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False


def check_status_exists(cadet_id):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Query to check if a record exists
        cursor.execute(
            """
            SELECT 
                status.status_id
            FROM 
                srt_info
            JOIN cadet ON srt_info.cadet_id = cadet.cadet_id
            JOIN status ON srt_info.status_id = status.status_id
            WHERE cadet.cadet_id = ?
            ORDER BY 
            srt_info.created_on DESC
            LIMIT 1
            """,
            (cadet_id,)
        )

        result = cursor.fetchone()
        # print(result)
        # print(type(result))

        if result is None:
            print(f"No status found for cadet_id: {cadet_id}")
            conn.close()
            return None  # Return None explicitly if no record exists

        result = result[0]
        # print(result)

        # print(type(result))
        conn.close()
        return result

        # Return True if a record exists, False otherwise

    except sqlite3.Error as e:
        print(f"Database error for checking status exists: {e}")
        return False


def delete_srt_info_by_cadet_id(cadet_id):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()

        query = """
        DELETE FROM srt_info
        WHERE cadet_id = ?
        """
        cursor.execute(query, (cadet_id,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False


def get_group_chat_id(group_chat_id):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()

        query = """
        SELECT tele_id
        FROM 'group'
        WHERE tele_id = ?
        """
        cursor.execute(query, (group_chat_id,))
        rows = cursor.fetchone()

        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None


def get_group_id(tele_group_chat_id):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()

        query = """
        SELECT group_id
        FROM 'group'
        WHERE tele_id = ?
        """
        cursor.execute(query, (tele_group_chat_id,))
        rows = cursor.fetchone()

        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None


def add_group(group_chat_id, name):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()

        query = """
        INSERT INTO 'group' (tele_id, name)
        VALUES (?, ?)
        """
        cursor.execute(query, (group_chat_id, name))
        conn.commit()

        conn.close()
        print("Group added successfully")
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False


def check_if_cadet_in_no_group(cadet_id):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()

        query = """
        SELECT *
        FROM cadet_group
        WHERE cadet_id = ?
        AND group_id = 1
        """
        cursor.execute(query, (cadet_id,))
        rows = cursor.fetchall()

        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None


def insert_cadet_into_no_group(cadet_id):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()

        query = """
        INSERT INTO cadet_group (cadet_id, group_id)
        VALUES (?, 1)
        """
        cursor.execute(query, (cadet_id,))
        conn.commit()

        conn.close()
        print("User inserted into no group successfully")
        return True
    except sqlite3.Error as e:
        print(f"Database error line 430: {e}")
        return False


def check_if_cadet_in_group(cadet_id, group_id):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()

        query = """
        SELECT *
        FROM cadet_group
        WHERE cadet_id = ?
        AND group_id = ?
        """
        cursor.execute(query, (cadet_id, group_id))
        rows = cursor.fetchall()

        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None


def add_cadet_group(cadet_id, group_id):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()

        query = """
        INSERT INTO cadet_group (cadet_id, group_id)
        VALUES (?, ?)
        """
        cursor.execute(query, (cadet_id, group_id))
        conn.commit()

        conn.close()
        print("cadet added to group successfully")
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False


def get_all_cadets_act_1_info():
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()

        query = """
        SELECT 
            cadet.name AS cadet_name,
            STRFTIME('%H%M', srt_info.datetime_in)
        FROM 
            srt_info
        JOIN 
            cadet ON srt_info.cadet_id = cadet.cadet_id
        JOIN 
            activity ON srt_info.activity_id = activity.activity_id
        JOIN
            status ON srt_info.status_id = status.status_id
        WHERE
            activity.activity_id = 1 AND status.status_id != 3
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None


def get_all_cadets_act_2_info():
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()

        query = """
        SELECT 
            cadet.name AS cadet_name,
            STRFTIME('%H%M', srt_info.datetime_in)
        FROM 
            srt_info
        JOIN 
            cadet ON srt_info.cadet_id = cadet.cadet_id
        JOIN
            status ON srt_info.status_id = status.status_id
        JOIN 
            activity ON srt_info.activity_id = activity.activity_id
        WHERE
            activity.activity_id = 2 AND status.status_id != 3
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None


def get_all_cadets_act_3_info():
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()

        query = """
        SELECT 
            cadet.name AS cadet_name,
            STRFTIME('%H%M', srt_info.datetime_in)
        FROM 
            srt_info
        JOIN 
            cadet ON srt_info.cadet_id = cadet.cadet_id
        JOIN
            status ON srt_info.status_id = status.status_id
        JOIN 
            activity ON srt_info.activity_id = activity.activity_id
        WHERE
            activity.activity_id = 3 AND status.status_id != 3
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None


def get_all_cadets_act_4_info():
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()

        query = """
        SELECT 
            cadet.name AS cadet_name,
            STRFTIME('%H%M', srt_info.datetime_in)
        FROM 
            srt_info
        JOIN 
            cadet ON srt_info.cadet_id = cadet.cadet_id
        JOIN
            status ON srt_info.status_id = status.status_id
        JOIN 
            activity ON srt_info.activity_id = activity.activity_id
        WHERE
            activity.activity_id = 4 AND status.status_id != 3
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None


# Define state constants
START_ROUTES, srt, srt_INFORMATION, ENTER_NAME, AGAIN = range(5)

# Callback data constants
ONE, TWO, THREE, FOUR, FIVE, SIX = range(6)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a welcome message and show the main menu."""
    chat_type = update.message.chat.type
    context.user_data["chat_type"] = chat_type

    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)

    telegram_id = user.id
    username = user.username
    context.user_data["telegram_id"] = telegram_id
    context.user_data["username"] = username

    existing_cadet = check_cadet_exists(telegram_id)
    if chat_type == "private":

        if existing_cadet:

            context.user_data["cadet_id"] = get_cadet_id_by_tele_id(
                context.user_data["telegram_id"])

            await update.message.reply_text(f"Welcome, {existing_cadet[0]}!")

            if has_srt_record_today(context.user_data['telegram_id']):

                cadet_id = get_cadet_id_by_tele_id(
                    context.user_data['telegram_id'])

                if check_status_exists(cadet_id) == 2:
                    keyboard = [
                        [
                            InlineKeyboardButton(
                                "Check Out SRT", callback_data=str(FIVE)),
                            InlineKeyboardButton(
                                "View SRT Details", callback_data=str(TWO)),
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text("What would you like to do?", reply_markup=reply_markup)

                elif check_status_exists(cadet_id) == 1:
                    keyboard = [
                        [
                            InlineKeyboardButton(
                                "Check In SRT", callback_data=str(THREE)),
                            InlineKeyboardButton(
                                "View SRT Details", callback_data=str(TWO)),
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text("What would you like to do?", reply_markup=reply_markup)
                elif check_status_exists(cadet_id) == 3:

                    # if datetime.now().hour < CUTOFF_TIME:
                    if datetime.now():
                        keyboard = [
                            [
                                InlineKeyboardButton(
                                    "Book SRT Slot", callback_data=str(ONE)),
                            ]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await update.message.reply_text("What would you like to do?", reply_markup=reply_markup)
                    else:
                        keyboard = [
                            [
                                InlineKeyboardButton(
                                    "Closed", callback_data='hi'),
                            ]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await update.message.reply_text("SRT bookings closed.", reply_markup=reply_markup)

            else:
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "Book SRT Slot", callback_data=str(ONE)),
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("What would you like to do?", reply_markup=reply_markup)

            return START_ROUTES

        else:
            # check if
            await update.message.reply_text("Welcome to the DIS SRT Bot! Please enter your full name:")

            return ENTER_NAME
    else:
        context.user_data['tg_group_chat_id'] = update.effective_message.chat_id
        context.user_data['chat_title'] = update.message.chat.title
        user = update.message.from_user
        telegram_id = user.id
        context.user_data["telegram_id"] = telegram_id
        context.user_data["cadet_id"] = get_cadet_id_by_tele_id(
            context.user_data["telegram_id"])
        current_date = datetime.now().strftime("%Y-%m-%d")

        if get_group_chat_id(context.user_data['tg_group_chat_id']) is None:
            add_group(
                context.user_data['tg_group_chat_id'], context.user_data['chat_title'])

        group_id = get_group_id(context.user_data['tg_group_chat_id'])
        if check_if_cadet_in_group(context.user_data['cadet_id'], group_id) == []:
            add_cadet_group(context.user_data['cadet_id'], group_id)

        all_cadets_act_1_info = get_all_cadets_act_1_info()
        all_cadets_act_2_info = get_all_cadets_act_2_info()
        all_cadets_act_3_info = get_all_cadets_act_3_info()
        all_cadets_act_4_info = get_all_cadets_act_4_info()

        print(all_cadets_act_4_info)

        response = f"Cadets participating in SRT on {current_date}:\n\n"

        if all_cadets_act_1_info != []:
            act_1_info = "\n".join(
                f"{row[0]} | {'Not checked in' if row[1] is None else f'Started at {row[1]}'}"
                for row in all_cadets_act_1_info
            )
            response += f"Run - Wingline\n{act_1_info}\n\n"

        if all_cadets_act_2_info != []:
            act_2_info = "\n".join(
                f"{row[0]} | {'Not checked in' if row[1] is None else f'Started at {row[1]}'}"
                for row in all_cadets_act_2_info
            )
            response += f"Run - Yellow Cluster\n{act_2_info}\n\n"

        if all_cadets_act_3_info != []:
            act_3_info = "\n".join(
                f"{row[0]} | {'Not checked in' if row[1] is None else f'Started at {row[1]}'}"
                for row in all_cadets_act_3_info
            )
            response += f"Gym - Wingline\n{act_3_info}\n\n"

        if all_cadets_act_4_info != []:
            act_4_info = "\n".join(
                f"{row[0]} | {'Not checked in' if row[1] is None else f'Started at {row[1]}'}"
                for row in all_cadets_act_4_info
            )
            response += f"Basketball - Basketball Court\n{act_4_info}\n\n"

        # If no cadet information is available for all activities
        if response.strip() == f"Cadets participating in SRT on {current_date}:":
            if datetime.now().hour > CUTOFF_TIME:
                response = f"All cadets have checked out."
            else:
                response = f"No cadets participating in SRT."

        await update.message.reply_text(response.strip())


async def start_again(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton("Book SRT Slot", callback_data=str(ONE)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("What would you like to do?", reply_markup=reply_markup)

    return START_ROUTES


async def handle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the cadet's full name input and redirect to start."""
    cadet_name = update.message.text
    telegram_id = context.user_data["telegram_id"]
    username = context.user_data["username"]

    # Save the name to the database or validate
    insert_cadet(telegram_id, username, cadet_name)

    context.user_data["cadet_id"] = get_cadet_id_by_tele_id(
        context.user_data["telegram_id"])

    user_in_no_group = check_if_cadet_in_no_group(
        context.user_data['cadet_id'])
    print('line 619:', user_in_no_group)
    if user_in_no_group == []:
        insert_cadet_into_no_group(context.user_data['cadet_id'])

    # Redirect to the start function
    await update.message.reply_text("Thank you! Redirecting to the main menu...")
    return await start(update, context)


async def one(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the Book srt Slot option."""
    query = update.callback_query
    await query.answer()

    cadet_id = get_cadet_id_by_tele_id(context.user_data['telegram_id'])

    delete_srt_info_by_cadet_id(cadet_id)

    # Fetch activities and show them as buttons
    activities = get_activities()
    if not activities:
        await query.edit_message_text("No activities found in the database.")
        return START_ROUTES

    keyboard = [
        [InlineKeyboardButton(
            activity[1], callback_data=f"activity_{activity[0]}")]
        for activity in activities
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("What activity would you like to do?", reply_markup=reply_markup)

    return srt


async def two(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the View srt details option."""
    query = update.callback_query

    srt_info = get_srt_info(str(context.user_data["telegram_id"]))
    date = datetime.now().strftime("%d-%m-%y")

    if has_srt_record_today(context.user_data['telegram_id']):

        # print("status:",check_status_exists(context.user_data['telegram_id']))
        cadet_id = get_cadet_id_by_tele_id(context.user_data['telegram_id'])

        if check_status_exists(cadet_id) == 2:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "Check Out SRT", callback_data=str(FIVE)),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"SRT Information:\n{srt_info}", reply_markup=reply_markup)

        elif check_status_exists(cadet_id) == 1:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "Check In SRT", callback_data=str(THREE)),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"SRT Information for {date}:\n{srt_info}", reply_markup=reply_markup)
        elif check_status_exists(cadet_id) == 3:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "Book SRT Slot", callback_data=str(ONE)),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"SRT Information for {date}:\n{srt_info}", reply_markup=reply_markup)

    else:
        keyboard = [
            [
                InlineKeyboardButton("Book SRT Slot", callback_data=str(ONE)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"SRT Information:\n{srt_info}", reply_markup=reply_markup)

    return START_ROUTES


async def activity_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle activity selection and go back to the main menu."""
    query = update.callback_query
    await query.answer()

    activity_id = int(query.data.split("_")[1])
    context.user_data["activity_id"] = activity_id
    created_on = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    await query.edit_message_text(f"SRT booking submitted.")
    insert_srt_info(context.user_data["cadet_id"],
                    activity_id, None, None, created_on, 1)  # 1'Pending'

    keyboard = [
        [
            InlineKeyboardButton("Check In SRT", callback_data=str(THREE)),
            InlineKeyboardButton("View SRT Details", callback_data=str(TWO)),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("What would you like to do?", reply_markup=reply_markup)

    return START_ROUTES


async def check_in(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Restart the conversation from the main menu."""
    query = update.callback_query
    await query.answer()

    existing_cadet = check_cadet_exists(context.user_data['telegram_id'])

    cadet_id = get_cadet_id_by_tele_id(context.user_data['telegram_id'])
    datetime_in = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    srt_check_in(datetime_in, 2, cadet_id)

    # print(check_status_exists(cadet_id))
    if check_status_exists(cadet_id) == 2:
        keyboard = [
            [
                InlineKeyboardButton("Check Out SRT", callback_data=str(FIVE)),
                InlineKeyboardButton("View SRT details",
                                     callback_data=str(TWO)),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("You have commenced your SRT.", reply_markup=reply_markup)


async def check_out(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Restart the conversation from the main menu."""
    query = update.callback_query
    await query.answer()

    cadet_id = get_cadet_id_by_tele_id(context.user_data['telegram_id'])
    datetime_out = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    srt_check_out(datetime_out, 3, cadet_id)

    keyboard = [
        [
            InlineKeyboardButton("Back to Main Menu",
                                 callback_data=str(SIX)),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("You have ended your SRT.", reply_markup=reply_markup)

    return AGAIN


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End the conversation."""
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Goodbye!")
    return ConversationHandler.END


def main():
    """Run the bot."""
    app = Application.builder().token(
        "7561336720:AAEuDMvGeY9Vn1VUSQ-nnPS-SYUxhOrsprI").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_ROUTES: [

                CallbackQueryHandler(one, pattern="^" + str(ONE) + "$"),
                CallbackQueryHandler(two, pattern="^" + str(TWO) + "$"),
                CallbackQueryHandler(check_in, pattern="^" + str(THREE) + "$"),
                CallbackQueryHandler(check_out, pattern="^" + str(FIVE) + "$"),
            ],
            srt: [
                CallbackQueryHandler(activity_selection, pattern="^activity_"),
                # CallbackQueryHandler(start_over, pattern="^" + str(ONE) + "$"),
                CallbackQueryHandler(end, pattern="^" + str(TWO) + "$"),
            ],
            ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name_input)],
            AGAIN: [CallbackQueryHandler(
                start_again, pattern="^" + str(SIX) + "$"),]

        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == "__main__":
    main()
