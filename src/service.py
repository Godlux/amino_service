import os
import amino
import yaml
import random
import time
import traceback

from functools import partial
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
from termcolor import colored
from string import ascii_letters
from .config import get_accounts, get_devices, get_count, \
    get_reg_devices, get_comments, set_pool_count, \
    set_accounts, get_auth_data, set_auth_data


class Login:
    def __init__(self):
        self.client = amino.Client()

    def login_sid(self, account: dict):
        email = account.get("email")
        sid = account.get("sid")
        while True:
            try:
                self.client.login_sid(sid)
                return self.client
            except amino.exceptions.ActionNotAllowed:
                self.client.device_id = random.choice(get_devices()).replace("\n", "")
            except amino.exceptions.FailedLogin:
                print(Log().align(email, "Failed login"))
                return False
            except amino.exceptions.InvalidAccountOrPassword:
                print(Log().align(email, "Invalid account or password"))
                return False
            except amino.exceptions.InvalidPassword:
                print(Log().align(email, "Invalid Password"))
                return False
            except amino.exceptions.InvalidEmail:
                print(Log().align(email, "Invalid Email"))
                return False
            except amino.exceptions.AccountDoesntExist:
                print(Log().align(email, "Account does not exist"))
                return False
            except amino.exceptions.VerificationRequired as verify:
                print(Log().align(email, str(verify)))
                return False
            except amino.exceptions.InvalidSession:
                print(Log().align(email, "SID update required..."))
                return False
            except Exception as e:
                print(Log().align(email, str(e)))
                return False

    def login(self, account: dict):
        email = account.get("email")
        password = account.get("password")
        while True:
            try:
                self.client.login(email, password)
                return self.client
            except amino.exceptions.ActionNotAllowed:
                self.client.device_id = random.choice(get_devices()).replace("\n", "")
            except amino.exceptions.FailedLogin:
                print(Log().align(email, "Failed login"))
                return False
            except amino.exceptions.InvalidAccountOrPassword:
                print(Log().align(email, "Invalid account or password"))
                return False
            except amino.exceptions.InvalidPassword:
                print(Log().align(email, "Invalid Password"))
                return False
            except amino.exceptions.InvalidEmail:
                print(Log().align(email, "Invalid Email"))
                return False
            except amino.exceptions.AccountDoesntExist:
                print(Log().align(email, "Account does not exist"))
                return False
            except amino.exceptions.VerificationRequired as verify:
                print(Log().align(email, str(verify)))
                return False
            except amino.exceptions.InvalidSession:
                print(Log().align(email, "InvalidSession"))
                return False
            except Exception as e:
                print(Log().align(email, str(e)))
                return False

    def check_sid(self):
        print("Checking accounts...")
        accounts = get_accounts()
        bad_accounts = []
        if accounts:
            for account in accounts:
                if account:
                    if account.get("sid") is None:
                        bad_accounts.append(account)
                else:
                    accounts.remove(account)
            for account in bad_accounts:
                accounts.remove(account)
            if bad_accounts:
                print(f"{len(bad_accounts)} bad accounts detected. Starting fix...")
                pool = Pool(set_pool_count())
                sid_pool = pool.map(self.login, bad_accounts)
                for client, account in zip(sid_pool, bad_accounts):
                    if client:
                        accounts.append({"email": account.get("email"), "password": account.get("password"), "uid": client.profile.userId, "sid": client.sid})
                if accounts:
                    set_accounts(accounts)
        else:
            print(colored("bots.yaml is empty", "red"))

    def update_sid(self):
        print("Starting update...")
        pool = Pool(set_pool_count())
        sid_pool = pool.map(self.get_sid, get_accounts())
        for account in sid_pool:
            if not account:
                sid_pool.remove(account)
        set_accounts(sid_pool)

    def get_sid(self, account: dict):
        client = self.login(account)
        if client:
            print(Log().align(account.get("email"), "SID updated"))
            return {"email": account.get("email"), "password": account.get("password"), "sid": client.sid, "uid": client.profile.userId}
        else:
            return False


class Register:
    def __init__(self):
        self.client = amino.Client()
        self.email = None
        self.password = input("Set a password for all accounts: ")
        while len(self.password) < 6:
            print(colored("Password must be at least 6 characters long", "red"))
            self.password = input("Set a password for all accounts: ")
        self.current_device = None
        self.code = None

    def run(self):
        if get_reg_devices():
            for device in get_reg_devices():
                self.current_device = device.replace("\n", "")
                for _ in range(3):
                    self.email = input("Email: ")
                    if self.register():
                        self.client.request_verify_code(deviceId=self.current_device, email=self.email)
                        if self.verify():
                            if self.login():
                                if self.activate():
                                    self.save_account()
                                else:
                                    continue
                            else:
                                continue
                        else:
                            continue
                    else:
                        continue
        else:
            print(colored("reg_devices.txt is empty", "red"))

    def register(self):
        while True:
            try:
                nick = ''.join(random.choice(ascii_letters) for _ in range(random.randint(2, 5)))
                self.client.register(nickname=nick, email=self.email, password=str(self.password),
                                     deviceId=self.current_device)
                return True
            except amino.exceptions.AccountLimitReached:
                print(colored("AccountLimitReached", "red"))
                return False
            except amino.exceptions.InvalidEmail:
                print(colored("Invalid Email", "red"))
                return False
            except amino.exceptions.EmailAlreadyTaken:
                print(colored("EmailAlreadyTaken", "red"))
                self.email = input("Email: ")
            except amino.exceptions.UnsupportedEmail:
                print(colored("UnsupportedEmail", "red"))
                return False
            except amino.exceptions.CommandCooldown:
                print(colored("CommandCooldown", "red"))
                return False
            except amino.exceptions.VerificationRequired as e:
                input(str(e) + "\n\npress ENTER to continue...")
            except Exception as e:
                print(colored(str(e), "red"))
                return False

    def verify(self):
        while True:
            self.code = input("Code: ")
            try:
                self.client.verify(deviceId=self.current_device, email=self.email, code=self.code)
                return True
            except amino.exceptions.IncorrectVerificationCode:
                print(colored("IncorrectVerificationCode", "red"))
            except Exception as e:
                print(colored(str(e), "red"))
                return False

    def login(self):
        while True:
            try:
                self.client.login(email=self.email, password=self.password)
                return True
            except amino.exceptions.ActionNotAllowed:
                self.client.device_id = random.choice(get_devices()).replace("\n", "")
            except Exception as e:
                print(colored(str(e), "red"))
                return False

    def activate(self):
        while True:
            try:
                self.client.activate_account(email=self.email, code=self.code)
                return True
            except Exception as e:
                print(colored(str(e), "red"))
                return False

    def save_account(self):
        with open(os.getcwd() + "/src/accounts/new_accounts.yaml", "a") as accounts_file:
            yaml.dump({"email": self.email, "password": self.password}, accounts_file, Dumper=yaml.Dumper)


class Community:
    @staticmethod
    def select(client):
        sub_clients = client.sub_clients(start=0, size=100)
        print("Select the community:")
        for x, name in enumerate(sub_clients.name, 1):
            print(f"{x}. {name}")
        while True:
            choice_sub_client = input("Enter community number: ")
            try:
                return sub_clients.comId[int(choice_sub_client) - 1]
            except (IndexError, TypeError):
                print(colored("Invalid community number", "red"))

    @staticmethod
    def sub_client(com_id: str, userid: str):
        try:
            sub_client = amino.SubClient(comId=com_id, userId=userid)
            return sub_client
        except amino.exceptions.UserNotMemberOfCommunity:
            print("UserNotMemberOfCommunity")
            return False
        except amino.exceptions.UserUnavailable:
            print("UserUnavailable")
            return False
        except Exception as e:
            print(e)
            return False


class Chats:
    def __init__(self, client, com_id: str):
        self.sub_client = Community().sub_client(com_id, client.userId)

    def select(self):
        get_chats = self.sub_client.get_chat_threads(start=0, size=100)
        chat_list = []
        x = 0
        print("Select the chat:")
        for name, thread_type, chatid in zip(get_chats.title, get_chats.type, get_chats.chatId):
            if thread_type != 0:
                x += 1
                print(f"{x}. {name}")
                chat_list.append(chatid)
        while True:
            choice_chat = input("Enter chat number: ")
            try:
                return chat_list[int(choice_chat) - 1]
            except IndexError:
                print(colored("Invalid chat number", "red"))


class Log:
    @staticmethod
    def align(text: str, action: str):
        spaces = 30 - len(text)
        text = f"[{text}"
        for _ in range(spaces):
            text += " "
        text += f"]: {action}"
        return text


class ServiceApp:
    def __init__(self):
        single_management = SingleAccountManagement()
        multi_management = MultiAccountsManagement(single_management.com_id)
        chat_moderation = ChatModeration(single_management.client, single_management.com_id)
        while True:
            try:
                print(colored(open("src/draw/management_choice.txt", "r").read(), "cyan"))
                management_choice = input("Enter the number >>> ")
                if management_choice == "1":
                    while True:
                        print(colored(open("src/draw/account_management.txt", "r").read(), "cyan"))
                        choice = input("Enter the number >>> ")
                        if choice == "1":
                            quiz_link = input("Quiz link: ")
                            object_id = single_management.client.get_from_code(str(quiz_link.split('/')[-1])).objectId
                            single_management.play_quiz(object_id)
                            print("[PlayQuiz]: Finish.")
                        elif choice == "2":
                            single_management.unfollow_all()
                            print("[UnfollowAll]: Finish.")
                        elif choice == "3":
                            count = input("How many posts do you want to like?: ")
                            single_management.activity(int(count))
                            print("[Activity]: Finish.")
                        elif choice == "4":
                            single_management.follow_all()
                            print("[FollowAll]: Finish.")
                        elif choice == "5":
                            Register().run()
                            print("[Register]: Finish.")
                        elif choice == "b":
                            break
                elif management_choice == "2":
                    Login().check_sid()
                    while True:
                        print(colored(open("src/draw/bot_management.txt", "r").read(), "cyan"))
                        choice = input("Enter the number >>> ")
                        if choice == "1":
                            pool = Pool(set_pool_count())
                            result = pool.map(multi_management.play_lottery, get_accounts())
                            count_result = get_count(result)
                            print(f"Accounts: {count_result['accounts']}\nResult: +{count_result['count']} coins")
                            print("[PlayLottery]: Finish.")
                        elif choice == "2":
                            blog_link = input("Blog link: ")
                            object_id = single_management.client.get_from_code(str(blog_link.split('/')[-1])).objectId
                            pool = Pool(set_pool_count())
                            result = pool.map(partial(multi_management.send_coins, object_id), get_accounts())
                            count_result = get_count(result)
                            print(f"Accounts {count_result['accounts']}\nResult: +{count_result['count']} coins")
                            print("[SendCoins]: Finish.")
                        elif choice == "3":
                            blog_link = input("Blog link: ")
                            object_id = single_management.client.get_from_code(str(blog_link.split('/')[-1])).objectId
                            pool = Pool(set_pool_count())
                            pool.map(partial(multi_management.like_blog, object_id), get_accounts())
                            print("[LikeBlog]: Finish.")
                        elif choice == "4":
                            object_id = Chats(single_management.client, multi_management.com_id).select()
                            pool = Pool(set_pool_count())
                            pool.map(partial(multi_management.join_bots_to_chat, object_id), get_accounts())
                            print("[JoinBotsToChat]: Finish.")
                        elif choice == "5":
                            object_id = Chats(single_management.client, multi_management.com_id).select()
                            pool = Pool(set_pool_count())
                            pool.map(partial(multi_management.leave_bots_from_chat, object_id), get_accounts())
                        elif choice == "6":
                            object_id = Community().select(single_management.client)
                            pool = Pool(set_pool_count())
                            invite_link = None
                            if single_management.client.get_community_info(object_id).joinType == 2:
                                invite_link = input("Enter invite link/code: ")
                            pool.map(partial(multi_management.join_bots_to_community, invite_link), get_accounts())
                            print("[JoinBotsToCommunity]: Finish.")
                        elif choice == "7":
                            object_id = Chats(single_management.client, multi_management.com_id).select()
                            text = input("Message text: ")
                            pool = Pool(set_pool_count())
                            pool.map(partial(multi_management.send_message, object_id, text), get_accounts())
                            print("[SendMessage]: Finish.")
                        elif choice == "8":
                            user_link = input("Link to user: ")
                            object_id = single_management.client.get_from_code(str(user_link.split('/')[-1])).objectId
                            pool = Pool(set_pool_count())
                            pool.map(partial(multi_management.follow, object_id), get_accounts())
                            print("[Follow]: Finish.")
                        elif choice == "9":
                            user_link = input("Link to user: ")
                            object_id = single_management.client.get_from_code(str(user_link.split('/')[-1])).objectId
                            pool = Pool(set_pool_count())
                            pool.map(partial(multi_management.unfollow, object_id), get_accounts())
                            print("[Unfollow]: Finish.")
                        elif choice == "10":
                            pool = Pool(set_pool_count())
                            pool.map(multi_management.set_online_status, get_accounts())
                            print("[SetOnlineStatus]: Finish.")
                        elif choice == "s":
                            Login().update_sid()
                            print("[UpdateSIDs]: Finish.")
                        elif choice == "b":
                            break
                elif management_choice == "3":
                    while True:
                        print(colored(open("src/draw/chat_moderation.txt", "r").read(), "cyan"))
                        choice = input("Enter the number >>> ")
                        if choice == "1":
                            object_id = Chats(single_management.client, single_management.com_id).select()
                            count = input("Number of messages: ")
                            chat_moderation.clear_chat(object_id, int(count))
                            print("[ClearChat]: Finish.")
                        elif choice == "2":
                            object_id = Chats(single_management.client, single_management.com_id).select()
                            chat_moderation.save_chat_settings(object_id)
                            print("[SaveChatSettings]: Finish.")
                        elif choice == "3":
                            object_id = Chats(single_management.client, single_management.com_id).select()
                            chat_moderation.set_view_mode(object_id)
                            print("[SetViewMode]: Finish.")
                        elif choice == "b":
                            break
            except Exception as e:
                print(traceback.format_exc())
                print(colored(str(e), "red"))


class SingleAccountManagement:
    def __init__(self):
        auth_data = get_auth_data()
        if auth_data:
            self.client = Login().login(get_auth_data())
        else:
            while True:
                email = input("Email: ")
                password = input("Password: ")
                self.client = Login().login({"email": email, "password": password})
                if self.client is False:
                    print(colored("Failed login", "red"))
                else:
                    set_auth_data({"email": email, "password": password})
                    break
        print("Login was successful!")
        self.com_id = Community().select(self.client)

    def play_quiz(self, object_id: str):
        questions_list = []
        answers_list = []

        sub_client = Community().sub_client(self.com_id, self.client.userId)
        quiz_info = sub_client.get_blog_info(quizId=object_id).json
        questions = quiz_info["blog"]["quizQuestionList"]
        total_questions = quiz_info["blog"]["extensions"]["quizTotalQuestionCount"]

        for x, question in enumerate(questions, 1):
            print(f"[quiz][{x}/{total_questions}]: Choosing the right answer...")
            question_id = question["quizQuestionId"]
            answers = question["extensions"]["quizQuestionOptList"]
            for answer in answers:
                answer_id = answer["optId"]
                sub_client.play_quiz(quizId=object_id, questionIdsList=[question_id], answerIdsList=[answer_id])
                latest_score = sub_client.get_quiz_rankings(quizId=object_id).profile.latestScore
                if latest_score > 0:
                    print(f"[quiz][{x}/{total_questions}]: Answer found!")
                    questions_list.append(question_id)
                    answers_list.append(answer_id)
        for i in range(2):
            try:
                sub_client.play_quiz(quizId=object_id, questionIdsList=questions_list, answerIdsList=answers_list,
                                     quizMode=i)
            except amino.exceptions.InvalidRequest:
                pass
        print(f"[quiz]: Passed the quiz!")
        print(f"[quiz]: Score: {sub_client.get_quiz_rankings(quizId=object_id).profile.highestScore}")

    def unfollow_all(self):
        print("Unfollow all...")
        thread_pool = ThreadPool(40)
        sub_client = Community().sub_client(self.com_id, self.client.userId)
        while True:
            following_count = sub_client.get_user_info(userId=self.client.userId).followingCount
            if following_count > 0:
                for i in range(0, 1000, 100):
                    followings = sub_client.get_user_following(userId=self.client.userId, start=i, size=100)
                    if followings.userId:
                        for user_id in followings.userId:
                            thread_pool.apply(sub_client.unfollow, [user_id])
                    else:
                        break
            else:
                break

    def activity(self, count: int):
        print("Activity...")
        comments = get_comments()
        sub_client = Community().sub_client(self.com_id, self.client.userId)
        old_blogs = []
        liked = 0
        while liked <= count:
            recent_blogs = sub_client.get_recent_blogs(start=0, size=100)
            for blog_id, blog_type in zip(recent_blogs.blog.blogId, recent_blogs.blog.type):
                if blog_id not in old_blogs:
                    try:
                        sub_client.like_blog(blogId=blog_id)
                        liked += 1
                        if comments:
                            sub_client.comment(message=random.choice(comments), blogId=blog_id)
                            time.sleep(2.5)
                    except amino.exceptions.RequestedNoLongerExists:
                        sub_client.like_blog(wikiId=blog_id)
                        liked += 1
                        if comments:
                            sub_client.comment(message=random.choice(comments), wikiId=blog_id)
                            time.sleep(2.5)
                    old_blogs.append(blog_id)
            time.sleep(5)

    def follow_all(self):
        print("Subscribe...")
        sub_client = Community().sub_client(self.com_id, self.client.userId)
        for i in range(0, 20000, 100):
            users = sub_client.get_all_users(type="recent", start=i, size=100).profile.userId
            if users:
                try:
                    sub_client.follow(userId=users)
                except Exception as e:
                    print(e)
            else:
                break
        for i in range(0, 20000, 100):
            users = sub_client.get_online_users(start=i, size=100).profile.userId
            if users:
                try:
                    sub_client.follow(userId=users)
                except Exception as e:
                    print(e)
            else:
                break
        for i in range(0, 50000, 100):
            chats = sub_client.get_public_chat_threads(type="recommended", start=i, size=100).chatId
            if chats:
                for chatid in chats:
                    for x in range(0, 1000, 100):
                        users = sub_client.get_chat_users(chatId=chatid, start=x, size=100).userId
                        if users:
                            try:
                                sub_client.follow(userId=users)
                            except Exception as e:
                                print(e)
                        else:
                            break
            else:
                break


class MultiAccountsManagement:
    def __init__(self, com_id):
        self.com_id = com_id

    def play_lottery(self, account: dict):
        email = account.get("email")
        userid = account.get("uid")
        client = Login().login_sid(account)
        if client:
            sub_client = Community().sub_client(self.com_id, userid)
            if sub_client:
                try:
                    play = sub_client.lottery()
                    award = play.awardValue if play.awardValue else 0
                    print(Log().align(email, f"+{award} coins won"))
                    return int(award)
                except amino.exceptions.AlreadyPlayedLottery:
                    print(Log().align(email, "AlreadyPlayedLottery"))
                except amino.exceptions.YouAreBanned:
                    print(Log().align(email, "You are banned"))
                except amino.exceptions.InvalidSession:
                    print(Log().align(email, "SID update required..."))
                except Exception as e:
                    print(Log().align(email, str(e)))
            else:
                print(Log().align(email, "Community error"))

    def send_coins(self, object_id, account: dict):
        email = account.get("email")
        userid = account.get("uid")
        client = Login().login_sid(account)
        if client:
            sub_client = Community().sub_client(self.com_id, userid)
            if sub_client:
                try:
                    coins = int(client.get_wallet_info().totalCoins)
                    if coins != 0:
                        sub_client.send_coins(coins=coins, blogId=object_id)
                        print(Log().align(email, f"+{coins} coins"))
                        return coins
                    else:
                        print(Log().align(email, "NotEnoughCoins"))
                except amino.exceptions.NotEnoughCoins:
                    print(Log().align(email, "NotEnoughCoins"))
                except amino.exceptions.InvalidRequest:
                    print(Log().align(email, "InvalidRequest"))
                except amino.exceptions.YouAreBanned:
                    print(Log().align(email, "You are banned"))
                except amino.exceptions.InvalidSession:
                    print(Log().align(email, "SID update required..."))
                except Exception as e:
                    print(Log().align(email, str(e)))
            else:
                print(Log().align(email, "Community error"))

    def like_blog(self, object_id, account: dict):
        email = account.get("email")
        userid = account.get("uid")
        client = Login().login_sid(account)
        if client:
            sub_client = Community().sub_client(self.com_id, userid)
            if sub_client:
                try:
                    sub_client.like_blog(blogId=object_id)
                    print(Log().align(email, "Like"))
                except amino.exceptions.RequestedNoLongerExists:
                    sub_client.like_blog(wikiId=object_id)
                    print(Log().align(email, "Like"))
                except amino.exceptions.YouAreBanned:
                    print(Log().align(email, "You are banned"))
                except amino.exceptions.InvalidSession:
                    print(Log().align(email, "SID update required..."))
                except Exception as e:
                    print(Log().align(email, str(e)))
            else:
                print(Log().align(email, "Community error"))

    def join_bots_to_chat(self, object_id, account: dict):
        email = account.get("email")
        userid = account.get("uid")
        client = Login().login_sid(account)
        if client:
            sub_client = Community().sub_client(self.com_id, userid)
            if sub_client:
                try:
                    sub_client.join_chat(chatId=object_id)
                    print(Log().align(email, "Join"))
                except amino.exceptions.YouAreBanned:
                    print(Log().align(email, "You are banned"))
                except amino.exceptions.RemovedFromChat:
                    print(Log().align(email, "You are removed from this chatroom"))
                except amino.exceptions.InvalidSession:
                    print(Log().align(email, "SID update required..."))
                except Exception as e:
                    print(Log().align(email, str(e)))
            else:
                print(Log().align(email, "Community error"))

    def leave_bots_from_chat(self, object_id, account: dict):
        email = account.get("email")
        userid = account.get("uid")
        client = Login().login_sid(account)
        if client:
            sub_client = Community().sub_client(self.com_id, userid)
            if sub_client:
                try:
                    sub_client.leave_chat(chatId=object_id)
                    print(Log().align(email, "Leave"))
                except amino.exceptions.YouAreBanned:
                    print(Log().align(email, "You are banned"))
                except amino.exceptions.RemovedFromChat:
                    print(Log().align(email, "You are removed from this chatroom"))
                except amino.exceptions.InvalidSession:
                    print(Log().align(email, "SID update required..."))
                except Exception as e:
                    print(Log().align(email, str(e)))
            else:
                print(Log().align(email, "Community error"))

    def join_bots_to_community(self, inv_link=None, account: dict = None):
        email = account.get("email")
        client = Login().login_sid(account)
        if client:
            if inv_link:
                invitation_id = client.link_identify(code=str(inv_link.split("/")[-1])).get("invitationId")
                if invitation_id:
                    try:
                        client.join_community(comId=self.com_id, invitationId=invitation_id)
                        print(Log().align(email, "Join"))
                    except amino.exceptions.InvalidSession:
                        print(Log().align(email, "SID update required..."))
                    except Exception as e:
                        print(Log().align(email, str(e)))
            else:
                try:
                    client.join_community(comId=self.com_id)
                    print(Log().align(email, "Join"))
                except amino.exceptions.InvalidSession:
                    print(Log().align(email, "SID update required..."))
                except Exception as e:
                    print(Log().align(email, str(e)))

    def send_message(self, object_id, text, account: dict):
        email = account.get("email")
        userid = account.get("uid")
        client = Login().login_sid(account)
        if client:
            sub_client = Community().sub_client(self.com_id, userid)
            if sub_client:
                try:
                    sub_client.send_message(chatId=object_id, message=text)
                    print(Log().align(email, "Send"))
                except amino.exceptions.YouAreBanned:
                    print(Log().align(email, "You are banned"))
                except amino.exceptions.RemovedFromChat:
                    print(Log().align(email, "You are removed from this chatroom"))
                except amino.exceptions.ChatViewOnly:
                    print(Log().align(email, "Chat in view only mode"))
                except amino.exceptions.AccessDenied:
                    print(Log().align(email, "Access denied"))
                except amino.exceptions.InvalidSession:
                    print(Log().align(email, "SID update required..."))
                except Exception as e:
                    print(Log().align(email, str(e)))
            else:
                print(Log().align(email, "Community error"))

    def follow(self, object_id, account: dict):
        email = account.get("email")
        userid = account.get("uid")
        client = Login().login_sid(account)
        if client:
            sub_client = Community().sub_client(self.com_id, userid)
            if sub_client:
                try:
                    sub_client.follow(userId=object_id)
                    print(Log().align(email, "Follow"))
                except amino.exceptions.YouAreBanned:
                    print(Log().align(email, "You are banned"))
                except amino.exceptions.AccessDenied:
                    print(Log().align(email, "Access denied"))
                except amino.exceptions.BlockedByUser:
                    print(Log().align(email, "You are blocked by this user"))
                except amino.exceptions.InvalidSession:
                    print(Log().align(email, "SID update required..."))
                except Exception as e:
                    print(Log().align(email, str(e)))
            else:
                print(Log().align(email, "Community error"))

    def unfollow(self, object_id, account: dict):
        email = account.get("email")
        userid = account.get("uid")
        client = Login().login_sid(account)
        if client:
            sub_client = Community().sub_client(self.com_id, userid)
            if sub_client:
                try:
                    sub_client.unfollow(userId=object_id)
                    print(Log().align(email, "Unfollow"))
                except amino.exceptions.YouAreBanned:
                    print(Log().align(email, "You are banned"))
                except amino.exceptions.AccessDenied:
                    print(Log().align(email, "Access denied"))
                except amino.exceptions.BlockedByUser:
                    print(Log().align(email, "You are blocked by this user"))
                except amino.exceptions.InvalidSession:
                    print(Log().align(email, "SID update required..."))
                except Exception as e:
                    print(Log().align(email, str(e)))
            else:
                print(Log().align(email, "Community error"))

    def set_online_status(self, account: dict):
        email = account.get("email")
        userid = account.get("uid")
        client = Login().login_sid(account)
        if client:
            sub_client = Community().sub_client(self.com_id, userid)
            if sub_client:
                try:
                    sub_client.activity_status("on")
                    print(Log().align(email, "Online status is set"))
                except amino.exceptions.YouAreBanned:
                    print(Log().align(email, "You are banned"))
                except amino.exceptions.InvalidSession:
                    print(Log().align(email, "SID update required..."))
                except Exception as e:
                    print(Log().align(email, str(e)))
            else:
                print(Log().align(email, "Community error"))


class ChatModeration:
    def __init__(self, client, com_id):
        self.client = client
        self.com_id = com_id

    def clear_chat(self, chatid, count):
        print("Clearing chat...")
        pool = ThreadPool(40)
        deleted = 0
        next_page = None
        back = False
        sub_client = Community().sub_client(self.com_id, self.client.userId)
        chat = sub_client.get_chat_thread(chatId=chatid)
        admins = [*chat.coHosts, chat.author.userId]
        if self.client.userId in admins:
            while not back:
                messages = sub_client.get_chat_messages(chatId=chatid, size=100, pageToken=next_page)
                if messages.messageId:
                    next_page = messages.nextPageToken
                    for message_id in messages.messageId:
                        if deleted < count:
                            pool.apply_async(sub_client.delete_message, [chatid, message_id, False, None])
                            deleted += 1
                        else:
                            back = True
                            break
                else:
                    break
        else:
            print(colored("You don't have co-host/host rights to use this function", "red"))

    def save_chat_settings(self, chatid):
        if os.path.exists(os.path.join(os.getcwd(), "src", "chat_settings")):
            pass
        else:
            os.mkdir(os.path.join(os.getcwd(), "src", "chat_settings"))
        sub_client = Community().sub_client(self.com_id, self.client.userId)
        with open(os.path.join(os.getcwd(), "src", "chat_settings", f"{chatid}.txt"), "w", encoding="utf-8") as settings_file:
            chat = sub_client.get_chat_thread(chatId=chatid)
            data = "====================Title====================\n" \
                   f"{chat.title}\n\n" \
                   "===================Content===================\n" \
                   f"{chat.content}\n\n" \
                   "====================Icon====================\n" \
                   f"{chat.icon}\n\n" \
                   "=================Background=================\n" \
                   f"{chat.backgroundImage}\n\n"
            if chat.announcement:
                data += "================Announcement================\n"
                data += f"{chat.announcement}\n"
            if chat.userAddedTopicList:
                data += "================Tags================\n"
                for i in chat.userAddedTopicList:
                    data += f"{i.get('name')}\nColor: {i.get('style').get('backgroundColor')}\n"
            settings_file.write(data)
        print(colored(f"Settings saved in {os.path.join(os.getcwd(), 'src', 'chat_settings', f'{chatid}.txt')}", "green"))

    def set_view_mode(self, chatid):
        sub_client = Community().sub_client(self.com_id, self.client.userId)
        chat = sub_client.get_chat_thread(chatId=chatid)
        admins = [*chat.coHosts, chat.author.userId]
        if self.client.userId in admins:
            sub_client.edit_chat(chatId=chatid, viewOnly=True)
            print("Chat mode is set to view")
        else:
            print(colored("You don't have co-host/host rights to use this function", "red"))
