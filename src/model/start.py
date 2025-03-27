from eth_account import Account
from loguru import logger

import primp
import random
import asyncio
from src.degensoft.decryption import decrypt_private_key
from src.model.projects.mints.xl_meme.instance import XLMeme
from src.model.projects.other.onchaingm.instance import OnchainGm
from src.model.projects.stakings.teko_finance import TekoFinance
from src.model.projects.swaps.bebop import Bebop
from src.model.projects.swaps.gte import GteSwaps
from src.model.projects.mints.cap_app import CapApp
from src.model.megaeth.faucet import faucet
from src.model.projects.other.gte_faucet.instance import GteFaucet
from src.model.help.stats import WalletStats
from src.model.onchain.web3_custom import Web3Custom
from src.utils.client import create_client
from src.utils.config import Config
from src.model.database.db_manager import Database


class Start:
    def __init__(
        self,
        account_index: int,
        proxy: str,
        private_key: str,
        config: Config,
        password: str
    ):
        self.account_index = account_index
        self.proxy = proxy
        self.private_key = private_key
        self.config = config
        self.private_key_enc = private_key
        self.private_key = decrypt_private_key(private_key, password) if password else private_key

        self.session: primp.AsyncClient | None = None
        self.megaeth_web3: Web3Custom | None = None

        self.wallet = Account.from_key(self.private_key)
        self.wallet_address = self.wallet.address

    async def initialize(self):
        try:
            self.session = await create_client(
                self.proxy, self.config.OTHERS.SKIP_SSL_VERIFICATION
            )
            self.megaeth_web3 = await Web3Custom.create(
                self.account_index,
                self.config.RPCS.MEGAETH,
                self.config.OTHERS.USE_PROXY_FOR_RPC,
                self.proxy,
                self.config.OTHERS.SKIP_SSL_VERIFICATION,
            )

            return True
        except Exception as e:
            logger.error(f"{self.account_index} | Error: {e}")
            return False

    async def flow(self):
        try:
            try:
                wallet_stats = WalletStats(self.config, self.megaeth_web3)
                await wallet_stats.get_wallet_stats(
                    self.private_key, self.account_index
                )
            except Exception as e:
                pass

            db = Database()
            try:
                tasks = await db.get_wallet_pending_tasks(self.private_key_enc)
            except Exception as e:
                if "no such table: wallets" in str(e):
                    logger.error(
                        f"{self.account_index} | Database not created or wallets table not found"
                    )
                    return False
                else:
                    logger.error(
                        f"{self.account_index} | Error getting tasks from database: {e}"
                    )
                    raise

            if not tasks:
                logger.warning(
                    f"{self.account_index} | No pending tasks found in database for this wallet. Exiting..."
                )
                if self.megaeth_web3:
                    await self.megaeth_web3.cleanup()
                return True

            task_plan_msg = [f"{i+1}. {task['name']}" for i, task in enumerate(tasks)]
            logger.info(
                f"{self.account_index} | Task execution plan: {' | '.join(task_plan_msg)}"
            )

            completed_tasks = []
            failed_tasks = []

            # Выполняем задачи
            for task in tasks:
                task_name = task["name"]

                if task_name == "skip":
                    logger.info(f"{self.account_index} | Skipping task: {task_name}")
                    continue

                logger.info(f"{self.account_index} | Executing task: {task_name}")

                success = await self.execute_task(task_name)

                if success:
                    await db.update_task_status(
                        self.private_key_enc, task_name, "completed"
                    )
                    completed_tasks.append(task_name)
                    await self.sleep(task_name)
                else:
                    failed_tasks.append(task_name)
                    if not self.config.FLOW.SKIP_FAILED_TASKS:
                        logger.error(
                            f"{self.account_index} | Failed to complete task {task_name}. Stopping wallet execution."
                        )
                        break
                    else:
                        logger.warning(
                            f"{self.account_index} | Failed to complete task {task_name}. Skipping to next task."
                        )
                        await self.sleep(task_name)


            return len(failed_tasks) == 0

        except Exception as e:
            logger.error(f"{self.account_index} | Error: {e}")

            return False
        finally:
            # Cleanup resources
            try:
                if self.megaeth_web3:
                    await self.megaeth_web3.cleanup()
                logger.info(f"{self.account_index} | All sessions closed successfully")
            except Exception as e:
                logger.error(f"{self.account_index} | Error during cleanup: {e}")

    async def execute_task(self, task):
        """Execute a single task"""
        task = task.lower()

        if task == "faucet":
            return await faucet(
                self.session,
                self.account_index,
                self.config,
                self.wallet,
                self.proxy,
            )

        if task == "cap_app":
            cap_app = CapApp(
                self.account_index,
                self.session,
                self.megaeth_web3,
                self.config,
                self.wallet,
            )
            return await cap_app.mint_cUSD()

        if task == "bebop":
            bebop = Bebop(
                self.account_index,
                self.session,
                self.megaeth_web3,
                self.config,
                self.wallet,
                self.proxy,
                self.private_key,
            )
            return await bebop.swaps()
        if task == "gte_swaps":
            gte = GteSwaps(
                self.account_index,
                self.session,
                self.megaeth_web3,
                self.config,
                self.wallet,
                self.proxy,
                self.private_key,
            )
            return await gte.execute_swap()

        if task == "teko_finance":
            teko_finance = TekoFinance(
                self.account_index,
                self.session,
                self.megaeth_web3,
                self.config,
                self.wallet,
                self.proxy,
                self.private_key,
            )
            return await teko_finance.stake()
        
        if task == "teko_faucet":
            teko_finance = TekoFinance(
                self.account_index,
                self.session,
                self.megaeth_web3,
                self.config,
                self.wallet,
                self.proxy,
                self.private_key,
            )
            return await teko_finance.faucet()
        
        if task == "onchain_gm":
            onchain_gm = OnchainGm(
                self.account_index,
                self.session,
                self.megaeth_web3,
                self.config,
                self.wallet,
            )
            return await onchain_gm.GM()

        if task == "xl_meme":
            xl_meme = XLMeme(
                self.account_index,
                self.session,
                self.megaeth_web3,
                self.config,
                self.wallet,
            )
            return await xl_meme.buy_meme()

        if task == "gte_faucet":
            gte_faucet = GteFaucet(
                self.account_index,
                self.session,
                self.megaeth_web3,
                self.config,
                self.wallet,
            )
            return await gte_faucet.faucet()

        logger.error(f"{self.account_index} | Task {task} not found")
        return False

    async def sleep(self, task_name: str):
        """Делает рандомную паузу между действиями"""
        pause = random.randint(
            self.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[0],
            self.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[1],
        )
        logger.info(
            f"{self.account_index} | Sleeping {pause} seconds after {task_name}"
        )
        await asyncio.sleep(pause)
