from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
import yaml
from pathlib import Path
import asyncio


@dataclass
class SettingsConfig:
    THREADS: int
    ATTEMPTS: int
    ACCOUNTS_RANGE: Tuple[int, int]
    EXACT_ACCOUNTS_TO_USE: List[int]
    PAUSE_BETWEEN_ATTEMPTS: Tuple[int, int]
    PAUSE_BETWEEN_SWAPS: Tuple[int, int]
    RANDOM_PAUSE_BETWEEN_ACCOUNTS: Tuple[int, int]
    RANDOM_PAUSE_BETWEEN_ACTIONS: Tuple[int, int]
    RANDOM_INITIALIZATION_PAUSE: Tuple[int, int]
    TELEGRAM_USERS_IDS: List[int]
    TELEGRAM_BOT_TOKEN: str
    SEND_TELEGRAM_LOGS: bool
    SHUFFLE_WALLETS: bool
    WAIT_FOR_TRANSACTION_CONFIRMATION_IN_SECONDS: int


@dataclass
class FlowConfig:
    TASKS: List
    SKIP_FAILED_TASKS: bool


@dataclass
class FaucetConfig:
    SOLVIUM_API_KEY: str


@dataclass
class RpcsConfig:
    MEGAETH: List[str]


@dataclass
class OthersConfig:
    SKIP_SSL_VERIFICATION: bool
    USE_PROXY_FOR_RPC: bool


@dataclass
class BebopConfig:
    BALANCE_PERCENTAGE_TO_SWAP: List[int]
    SWAP_ALL_TO_ETH: bool

@dataclass
class GteConfig:
    BALANCE_PERCENTAGE_TO_SWAP: List[int]
    SWAP_ALL_TO_ETH: bool
    SWAPS_AMOUNT: List[int]

@dataclass
class TekoFinanceConfig:
    CHANCE_FOR_MINT_TOKENS: int
    BALANCE_PERCENTAGE_TO_STAKE: List[int]


@dataclass
class XLMemeConfig:
    BALANCE_PERCENTAGE_TO_BUY: List[float]
    CONTRACTS_TO_BUY: List[str]


@dataclass
class SwapsConfig:
    BEBOP: BebopConfig
    GTE: GteConfig

@dataclass
class StakingsConfig:
    TEKO_FINANCE: TekoFinanceConfig


@dataclass
class MintsConfig:
    XL_MEME: XLMemeConfig


@dataclass
class WalletInfo:
    account_index: int
    address: str
    balance: float
    transactions: int


@dataclass
class WalletsConfig:
    wallets: List[WalletInfo] = field(default_factory=list)


@dataclass
class Config:
    SETTINGS: SettingsConfig
    FLOW: FlowConfig
    FAUCET: FaucetConfig
    RPCS: RpcsConfig
    OTHERS: OthersConfig
    SWAPS: SwapsConfig
    STAKINGS: StakingsConfig
    MINTS: MintsConfig
    WALLETS: WalletsConfig = field(default_factory=WalletsConfig)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @classmethod
    def load(cls, path: str = "config.yaml") -> "Config":
        """Load configuration from yaml file"""
        with open(path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        # Load tasks from tasks.py
        try:
            import tasks

            if hasattr(tasks, "TASKS"):
                tasks_list = tasks.TASKS
            else:
                error_msg = "No TASKS list found in tasks.py"
                print(f"Error: {error_msg}")
                raise ValueError(error_msg)
        except ImportError as e:
            error_msg = f"Could not import tasks.py: {e}"
            print(f"Error: {error_msg}")
            raise ImportError(error_msg) from e

        return cls(
            SETTINGS=SettingsConfig(
                THREADS=data["SETTINGS"]["THREADS"],
                ATTEMPTS=data["SETTINGS"]["ATTEMPTS"],
                ACCOUNTS_RANGE=tuple(data["SETTINGS"]["ACCOUNTS_RANGE"]),
                EXACT_ACCOUNTS_TO_USE=data["SETTINGS"]["EXACT_ACCOUNTS_TO_USE"],
                PAUSE_BETWEEN_ATTEMPTS=tuple(
                    data["SETTINGS"]["PAUSE_BETWEEN_ATTEMPTS"]
                ),
                PAUSE_BETWEEN_SWAPS=tuple(data["SETTINGS"]["PAUSE_BETWEEN_SWAPS"]),
                RANDOM_PAUSE_BETWEEN_ACCOUNTS=tuple(
                    data["SETTINGS"]["RANDOM_PAUSE_BETWEEN_ACCOUNTS"]
                ),
                RANDOM_PAUSE_BETWEEN_ACTIONS=tuple(
                    data["SETTINGS"]["RANDOM_PAUSE_BETWEEN_ACTIONS"]
                ),
                RANDOM_INITIALIZATION_PAUSE=tuple(
                    data["SETTINGS"]["RANDOM_INITIALIZATION_PAUSE"]
                ),
                TELEGRAM_USERS_IDS=data["SETTINGS"]["TELEGRAM_USERS_IDS"],
                TELEGRAM_BOT_TOKEN=data["SETTINGS"]["TELEGRAM_BOT_TOKEN"],
                SEND_TELEGRAM_LOGS=data["SETTINGS"]["SEND_TELEGRAM_LOGS"],
                SHUFFLE_WALLETS=data["SETTINGS"].get("SHUFFLE_WALLETS", True),
                WAIT_FOR_TRANSACTION_CONFIRMATION_IN_SECONDS=data["SETTINGS"].get(
                    "WAIT_FOR_TRANSACTION_CONFIRMATION_IN_SECONDS", 120
                ),
                SHUFFLE_WALLETS=data["SETTINGS"].get("SHUFFLE_WALLETS", True),
            ),
            FLOW=FlowConfig(
                TASKS=tasks_list,
                SKIP_FAILED_TASKS=data["FLOW"]["SKIP_FAILED_TASKS"],
            ),
            FAUCET=FaucetConfig(
                SOLVIUM_API_KEY=data["FAUCET"]["SOLVIUM_API_KEY"],
            ),
            RPCS=RpcsConfig(
                MEGAETH=data["RPCS"]["MEGAETH"],
            ),
            OTHERS=OthersConfig(
                SKIP_SSL_VERIFICATION=data["OTHERS"]["SKIP_SSL_VERIFICATION"],
                USE_PROXY_FOR_RPC=data["OTHERS"]["USE_PROXY_FOR_RPC"],
            ),
            SWAPS=SwapsConfig(
                BEBOP=BebopConfig(
                    BALANCE_PERCENTAGE_TO_SWAP=data["SWAPS"]["BEBOP"][
                        "BALANCE_PERCENTAGE_TO_SWAP"
                    ],
                    SWAP_ALL_TO_ETH=data["SWAPS"]["BEBOP"]["SWAP_ALL_TO_ETH"],
                ),
                GTE=GteConfig(
                    BALANCE_PERCENTAGE_TO_SWAP=data["SWAPS"]["GTE"]["BALANCE_PERCENTAGE_TO_SWAP"],
                    SWAP_ALL_TO_ETH=data["SWAPS"]["GTE"]["SWAP_ALL_TO_ETH"],
                    SWAPS_AMOUNT=data["SWAPS"]["GTE"]["SWAPS_AMOUNT"],
                ),
            ),
            STAKINGS=StakingsConfig(
                TEKO_FINANCE=TekoFinanceConfig(
                    CHANCE_FOR_MINT_TOKENS=data["STAKINGS"]["TEKO_FINANCE"][
                        "CHANCE_FOR_MINT_TOKENS"
                    ],
                    BALANCE_PERCENTAGE_TO_STAKE=data["STAKINGS"]["TEKO_FINANCE"][
                        "BALANCE_PERCENTAGE_TO_STAKE"
                    ],
                ),
            ),
            MINTS=MintsConfig(
                XL_MEME=XLMemeConfig(
                    BALANCE_PERCENTAGE_TO_BUY=data["MINTS"]["XL_MEME"][
                        "BALANCE_PERCENTAGE_TO_BUY"
                    ],
                    CONTRACTS_TO_BUY=data["MINTS"]["XL_MEME"]["CONTRACTS_TO_BUY"],
                ),
            ),
        )

# Singleton pattern
def get_config() -> Config:
    """Get configuration singleton"""
    if not hasattr(get_config, "_config"):
        get_config._config = Config.load()
    return get_config._config
