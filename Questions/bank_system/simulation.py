"""
All your implementation code for the bank system simulation goes here.
"""

class Simulation:

    # Constant representing the number of milliseconds in one day.
    # This is used to schedule cashback refunds exactly 24 hours
    # after a payment is made.
    MILLISECONDS_IN_1_DAY = 86400000

    # The constructor initializes the core data structures used
    # by the banking simulation.
    #
    # self.accounts -> stores the current state of every active account
    # self.payments -> stores information about all payment transactions
    # self.payment_count -> used to generate unique payment IDs
    # self.history -> stores balance history snapshots for each account
    def __init__(self):
        self.accounts = {}
        self.payments = {}
        self.payment_count = 0 
        self.history = {}

    def create_account(self, timestamp: int, account_id: str) -> bool | None:
        # Before performing any operation we process pending cashbacks
        # so the system state is correct at this timestamp.
        self._process_cashbacks(timestamp)
        # If the account already exists, creation fails.
        if account_id in self.accounts:
            return False 
        # Initialize the account with balance 0 and outgoing 0.
        self.accounts[account_id] = {"balance" : 0, "outgoing": 0}
        # Record the initial balance snapshot for historical queries.
        self.history[account_id] = [(timestamp, 0)]

        return True

    def deposit(self, timestamp: int, account_id: str, amount: int) -> int | None:
        # Process any cashback events that should already have occurred.
        self._process_cashbacks(timestamp)
        # Deposits are only allowed on existing accounts.
        if account_id not in self.accounts:
            return None

        # Add the deposited amount to the account balance.
        self.accounts[account_id]["balance"] += amount
        # Record the new balance in the account history.
        self.history[account_id].append((timestamp, self.accounts[account_id]["balance"]))

        return self.accounts[account_id]["balance"]


    def transfer(self, timestamp: int, source_account_id: str, target_account_id: str, amount: int) -> int | None:
        # Ensure cashback updates are applied before the transfer.
        self._process_cashbacks(timestamp)
        # Transfers require both accounts to exist.
        if source_account_id not in self.accounts or target_account_id not in self.accounts: 
            return None
        
        # Prevent transferring money to the same account.
        if source_account_id == target_account_id:
            return None
        
        # The source account must have enough balance.
        if self.accounts[source_account_id]["balance"] < amount:
            return None
        
        # Deduct money from the source account and add it to the target.
        self.accounts[source_account_id]["balance"] -= amount
        self.accounts[source_account_id]["outgoing"] += amount
        self.accounts[target_account_id]["balance"] += amount

        # Record balance changes for both accounts.
        self.history[source_account_id].append((timestamp, self.accounts[source_account_id]["balance"]))
        self.history[target_account_id].append((timestamp, self.accounts[target_account_id]["balance"]))
        
        return self.accounts[source_account_id]["balance"]

    def top_spenders(self, timestamp: int, n: int) -> list[str] | None:
        # Ensure balances are up to date before computing rankings.
        self._process_cashbacks(timestamp)
        # Sort accounts by highest outgoing spending first.
        # If two accounts spent the same amount, sort by account ID.
        sorted_accounts = sorted (
            self.accounts.items(),
            key = lambda item: (-item[1]["outgoing"], item[0])
        )

        # Build the formatted output list.
        result = []
        for account_id, info in sorted_accounts[:n]:
            result.append(f"{account_id}({info['outgoing']})")

        return result
   
    def pay(self, timestamp: int, account_id: str, amount: int) -> str | None:
        # Apply cashback events before performing a new payment.
        self._process_cashbacks(timestamp)

        # Payments require a valid account.
        if account_id not in self.accounts:
            return None
        
        # Payment fails if the account does not have enough money.
        if self.accounts[account_id]["balance"] < amount:
            return None
        
        # Withdraw the payment amount immediately.
        self.accounts[account_id]["balance"] -= amount
        # Track total outgoing spending for top_spenders.
        self.accounts[account_id]["outgoing"] += amount

        # Record the new balance snapshot.
        self.history[account_id].append((timestamp, self.accounts[account_id]["balance"]))

        # Generate a unique payment identifier.
        self.payment_count += 1
        payment_id = f"payment{self.payment_count}"

        # Cashback is 2% of the payment amount, rounded down.
        cashback = amount * 2 // 100
        # Cashback will be refunded exactly 24 hours later.
        cashback_time = timestamp + self.MILLISECONDS_IN_1_DAY

        # Store payment information so its status and cashback
        # can be processed later.
        self.payments[payment_id] = {
            "account_id": account_id,
            "cashback": cashback,
            "cashback_time": cashback_time,
            "status": "IN_PROGRESS"
        }

        return payment_id


    def _process_cashbacks(self, timestamp: int) -> None:
        # Iterate through every recorded payment to see if
        # its cashback should be applied.
        for payment_id, payment_info in self.payments.items():
            # Cashback is processed only if the payment is still
            # IN_PROGRESS and its scheduled cashback time has arrived.
            if (payment_info["status"] == "IN_PROGRESS" and payment_info["cashback_time"] <= timestamp):
                # Identify which account should receive the refund.
                account_id = payment_info["account_id"]
                # Refund the cashback amount to the account balance.
                cashback = payment_info["cashback"]
                if account_id in self.accounts:
                    self.accounts[account_id]["balance"] += cashback
                    # Record the balance change at the cashback timestamp.
                    self.history[account_id].append((payment_info["cashback_time"], self.accounts[account_id]["balance"]))
                    # Mark the payment as completed once cashback is issued.
                    payment_info["status"] = "CASHBACK_RECEIVED"
                                          
    def get_payment_status(self, timestamp: int, account_id: str, payment: str) -> str | None:
        # Ensure cashback updates are applied before checking status.
        self._process_cashbacks(timestamp)

        # The account must exist.
        if account_id not in self.accounts:
            return None
       
        # The payment must exist.
        if payment not in self.payments:
            return None 
       
        # The payment must belong to the specified account.
        if self.payments[payment]["account_id"] != account_id:
            return None
       
        # Return the current status of the payment.
        return self.payments[payment]["status"]

    def merge_accounts(self, timestamp: int, account_id_1: str, account_id_2: str) -> bool | None:
        # First, process any cashback that should already have happened
        # before this merge timestamp.
        self._process_cashbacks(timestamp)
        
        # You cannot merge an account into itself.
        if account_id_1 == account_id_2:
            return False
        
        # Both accounts must exist for the merge to work.
        if account_id_1 not in self.accounts or account_id_2 not in self.accounts:
            return False 
        
        # Add account 2's balance into account 1.
        self.accounts[account_id_1]["balance"] += self.accounts[account_id_2]["balance"]

        # Add account 2's outgoing total into account 1
        # so top_spenders reflects the merged account correctly.  
        self.accounts[account_id_1]["outgoing"] += self.accounts[account_id_2]["outgoing"]

        # Any payment that used to belong to account 2 should now belong
        # to account 1, because account 2 will no longer exist.        
        for payment in self.payments.values():
            if payment["account_id"] == account_id_2:
                payment["account_id"] = account_id_1

        # Copy account 2's balance history into account 1's history
        # so account 1 inherits account 2's transaction history.
        self.history[account_id_1].extend(self.history[account_id_2])

        # Record the new merged balance at the merge timestamp.
        self.history[account_id_1].append((timestamp, self.accounts[account_id_1]["balance"]))

        # Remove account 2 from the active system.
        del self.accounts[account_id_2]
        del self.history[account_id_2]

        # Merge succeeded.
        return True

    def get_balance(self, timestamp: int, account_id: str, time_at: int) -> int | None:
        # Process cashback events first so any balance changes that should
        # already exist are reflected in history before we answer.
        self._process_cashbacks(timestamp)

        # If we do not have any balance history for this account,
        # then the account does not exist in the system.
        if account_id not in self.history:
            return None

        balance = None

        # Look through the account's history in time order and keep
        # updating balance while the snapshot happened at or before time_at.
        for snapshot_time, snapshot_balance in sorted(self.history[account_id]):
            if snapshot_time <= time_at:
                balance = snapshot_balance
            else:
                break

        return balance
