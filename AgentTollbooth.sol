// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AgentTollbooth
 * @notice High-throughput Micro-Payment Clearing & Tollbooth Contract for Autonomous AI Agents.
 * @dev Enables sub-cent agent-to-agent (A2A) micro-payments via off-chain EIP-712 signed vouchers.
 */

interface IERC20 {
    function transfer(address recipient, uint256 amount) external returns (bool);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract AgentTollbooth {
    address public immutable owner;
    uint256 public tollFeeBps; // e.g. 250 = 2.5%
    uint256 public constant MAX_BPS = 10000;

    // Balances deposited by agents for gasless micro-streaming: agent => token => balance
    mapping(address => mapping(address => uint256)) public agentBalances;

    // Nonce tracking to prevent replay attacks: agent => nonce
    mapping(address => uint256) public agentNonces;

    // Cumulative fees collected: token => amount
    mapping(address => uint256) public accumulatedTollFees;

    uint256 public totalTransactionsCleared;
    uint256 public totalVolumeClearedUSD;

    bytes32 public immutable DOMAIN_SEPARATOR;
    bytes32 public constant VOUCHER_TYPEHASH = keccak256(
        "MicroVoucher(address agent,address provider,address token,uint256 amount,uint256 nonce,uint256 deadline)"
    );

    event AgentDeposited(address indexed agent, address indexed token, uint256 amount);
    event AgentWithdrawn(address indexed agent, address indexed token, uint256 amount);
    event MicroPaymentCleared(
        address indexed agent,
        address indexed provider,
        address indexed token,
        uint256 grossAmount,
        uint256 tollFee,
        uint256 netProviderAmount,
        uint256 nonce
    );
    event TollFeesClaimed(address indexed token, uint256 amount, address indexed recipient);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner authorized");
        _;
    }

    constructor(uint256 _initialTollBps) {
        require(_initialTollBps <= 1000, "Max toll 10%");
        owner = msg.sender;
        tollFeeBps = _initialTollBps;

        DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
                keccak256(bytes("AgentTollbooth")),
                keccak256(bytes("1")),
                block.chainid,
                address(this)
            )
        );
    }

    function deposit(address token, uint256 amount) external {
        require(amount > 0, "Amount > 0");
        require(IERC20(token).transferFrom(msg.sender, address(this), amount), "Transfer failed");
        agentBalances[msg.sender][token] += amount;
        emit AgentDeposited(msg.sender, token, amount);
    }

    function withdraw(address token, uint256 amount) external {
        require(agentBalances[msg.sender][token] >= amount, "Insufficient balance");
        agentBalances[msg.sender][token] -= amount;
        require(IERC20(token).transfer(msg.sender, amount), "Transfer failed");
        emit AgentWithdrawn(msg.sender, token, amount);
    }

    /**
     * @notice Settles an off-chain signed micro-voucher.
     */
    function settleVoucher(
        address agent,
        address provider,
        address token,
        uint256 amount,
        uint256 deadline,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        require(block.timestamp <= deadline, "Voucher expired");
        require(agentBalances[agent][token] >= amount, "Agent balance depleted");

        uint256 nonce = agentNonces[agent]++;

        bytes32 digest = keccak256(
            abi.encodePacked(
                "\x19\x01",
                DOMAIN_SEPARATOR,
                keccak256(abi.encode(VOUCHER_TYPEHASH, agent, provider, token, amount, nonce, deadline))
            )
        );

        require(ecrecover(digest, v, r, s) == agent, "Invalid voucher signature");

        // Deduct from agent
        agentBalances[agent][token] -= amount;

        // Calculate toll
        uint256 toll = (amount * tollFeeBps) / MAX_BPS;
        uint256 netProvider = amount - toll;

        accumulatedTollFees[token] += toll;
        totalTransactionsCleared++;
        totalVolumeClearedUSD += amount;

        require(IERC20(token).transfer(provider, netProvider), "Payout failed");

        emit MicroPaymentCleared(agent, provider, token, amount, toll, netProvider, nonce);
    }

    function claimTollFees(address token, address recipient) external onlyOwner {
        uint256 fees = accumulatedTollFees[token];
        require(fees > 0, "No fees");
        accumulatedTollFees[token] = 0;
        require(IERC20(token).transfer(recipient, fees), "Transfer failed");
        emit TollFeesClaimed(token, fees, recipient);
    }

    function setTollFeeBps(uint256 newBps) external onlyOwner {
        require(newBps <= 1000, "Max toll 10%");
        tollFeeBps = newBps;
    }
}
