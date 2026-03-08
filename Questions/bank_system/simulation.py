"""
All your implementation code for the bank system simulation goes here.
"""

class Simulation:

    MILLISECONDS_IN_1_DAY = 86400000

    def __init__(self):
        self.accounts = {}
        self.payments = {}
        self.payment_counter = 1
        self.balance_history = {}

    def create_account(self, timestamp: int, account_id: str) -> bool | None:
        self._process_cashbacks(timestamp)
        if account_id in self.accounts:
            return False
        self.accounts[account_id] = {"balance": 0, "outgoing": 0}
        self.balance_history[account_id] = [(timestamp,0)]
        return True

    def deposit(self, timestamp: int, account_id: str, amount: int) -> int | None:
        self._process_cashbacks(timestamp)

        if account_id not in self.accounts:
            return None
        self.accounts[account_id]["balance"] += amount
        self._record_balance(timestamp, account_id)
        return self.accounts[account_id]["balance"]

    def transfer(self, timestamp: int, source_account_id: str, target_account_id: str, amount: int) -> int | None:
        self._process_cashbacks(timestamp)

        if source_account_id not in self.accounts or target_account_id not in self.accounts:
            return None

        if source_account_id == target_account_id:
            return None

        if self.accounts[source_account_id]["balance"] < amount:
            return None

        self.accounts[source_account_id]["balance"] -= amount
        self.accounts[source_account_id]["outgoing"] += amount
        self.accounts[target_account_id]["balance"] += amount

        self._record_balance(timestamp, source_account_id)
        self._record_balance(timestamp, target_account_id)

        return self.accounts[source_account_id]["balance"]

    def top_spenders(self, timestamp: int, n: int) -> list[str] | None:
        self._process_cashbacks(timestamp)

        sorted_accounts = sorted(
            self.accounts.items(),
            key=lambda item: (-item[1]["outgoing"], item[0])
        )

        result = []
        for account_id, info in sorted_accounts[:n]:
            result.append(f"{account_id}({info['outgoing']})")

        return result

    def pay(self, timestamp: int, account_id: str, amount: int) -> str | None:
        self._process_cashbacks(timestamp)

        if account_id not in self.accounts:
            return None

        if self.accounts[account_id]["balance"] < amount:
            return None

        self.accounts[account_id]["balance"] -= amount
        self.accounts[account_id]["outgoing"] += amount
        self._record_balance(timestamp, account_id)

        payment_id = f"payment{self.payment_counter}"
        self.payment_counter += 1

        cashback = amount * 2 // 100
        cashback_time = timestamp + self.MILLISECONDS_IN_1_DAY
        self.payments[payment_id] = {
            "account_id": account_id,
            "amount": amount,
            "status": "IN_PROGRESS",
            "cashback": cashback,
            "cashback_time": cashback_time
        }

        return payment_id

    def _record_balance(self, timestamp: int, account_id: str):
        self.balance_history[account_id].append(
            (timestamp, self.accounts[account_id]["balance"])
        )

    def _process_cashbacks(self, timestamp: int) -> None:
        for payment_id, payment_info in self.payments.items():
            if (
                payment_info["status"] == "IN_PROGRESS"
                and payment_info["cashback_time"] <= timestamp
            ):
                account_id = payment_info["account_id"]

                if account_id in self.accounts:
                    self.accounts[account_id]["balance"] += payment_info["cashback"]
                    self._record_balance(payment_info["cashback_time"], account_id)

                payment_info["status"] = "CASHBACK_RECEIVED"

    def get_payment_status(self, timestamp: int, account_id: str, payment: str) -> str | None:
        self._process_cashbacks(timestamp)

        if account_id not in self.accounts:
            return None

        if payment not in self.payments:
            return None

        if self.payments[payment]["account_id"] != account_id:
            return None

        return self.payments[payment]["status"]

    def merge_accounts(self, timestamp: int, account_id_1: str, account_id_2: str) -> bool | None:
        self._process_cashbacks(timestamp)

        if account_id_1 not in self.accounts or account_id_2 not in self.accounts:
            return False

        if account_id_1 == account_id_2:
            return False

        self.accounts[account_id_1]["balance"] += self.accounts[account_id_2]["balance"]
        self.accounts[account_id_1]["outgoing"] += self.accounts[account_id_2]["outgoing"]

        for payment_info in self.payments.values():
            if payment_info["account_id"] == account_id_2:
                payment_info["account_id"] = account_id_1

        self._record_balance(timestamp, account_id_1)

        del self.accounts[account_id_2]
        del self.balance_history[account_id_2]

        return True

    def get_balance(self, timestamp: int, account_id: str, time_at: int) -> int | None:
        self._process_cashbacks(timestamp)

        if account_id not in self.balance_history:
            return None

        balance = None
        for recorded_time, recorded_balance in self.balance_history[account_id]:
            if recorded_time <= time_at:
                balance = recorded_balance
            else:
                break

        return balance
