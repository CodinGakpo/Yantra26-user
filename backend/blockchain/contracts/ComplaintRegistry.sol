// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ComplaintRegistry
 * @notice Immutable complaint lifecycle event logging with SLA enforcement
 * @dev This contract acts as a tamper-proof audit trail for complaint management
 * 
 * Design Principles:
 * - Events for logging (not on-chain arrays) - cheaper gas, easier indexing
 * - Minimal on-chain storage - only what's needed for verification
 * - No personal data on-chain - only hashes and references
 * - SLA logic enforced by contract, not application layer
 */
contract ComplaintRegistry {
    
    // ============ State Variables ============
    
    address public owner;
    
    // Mapping: complaint_id => SLA deadline (Unix timestamp)
    mapping(string => uint256) public slaDeadlines;
    
    // Mapping: complaint_id => escalation status
    mapping(string => bool) public isEscalated;
    
    // Mapping: complaint_id => array of event hashes (for verification)
    mapping(string => bytes32[]) private complaintEventHashes;
    
    // Mapping: complaint_id => mapping(evidence_hash => block.timestamp)
    mapping(string => mapping(bytes32 => uint256)) public evidenceRegistry;
    
    // ============ Events ============
    
    /**
     * @notice Emitted when a complaint lifecycle event occurs
     * @dev Off-chain systems should listen to this event
     */
    event ComplaintEvent(
        string indexed complaintId,
        string eventType,
        bytes32 eventHash,
        uint256 timestamp
    );
    
    /**
     * @notice Emitted when evidence is anchored on-chain
     */
    event EvidenceAnchored(
        string indexed complaintId,
        bytes32 evidenceHash,
        uint256 timestamp
    );
    
    /**
     * @notice Emitted when a complaint is escalated due to SLA breach
     */
    event ComplaintEscalated(
        string indexed complaintId,
        uint256 deadline,
        uint256 escalationTime
    );
    
    /**
     * @notice Emitted when SLA deadline is set or updated
     */
    event SLADeadlineSet(
        string indexed complaintId,
        uint256 deadline
    );
    
    // ============ Modifiers ============
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    modifier validComplaintId(string memory complaintId) {
        require(bytes(complaintId).length > 0, "Complaint ID cannot be empty");
        _;
    }
    
    // ============ Constructor ============
    
    constructor() {
        owner = msg.sender;
    }
    
    // ============ Core Functions ============
    
    /**
     * @notice Log a complaint lifecycle event
     * @dev This is the primary function for immutable audit trail
     * @param complaintId Unique identifier for the complaint
     * @param eventType Type of event (CREATED, ASSIGNED, STATUS_UPDATED, etc.)
     * @param eventHash Keccak256 hash of the off-chain event payload
     */
    function logComplaintEvent(
        string memory complaintId,
        string memory eventType,
        bytes32 eventHash
    ) external validComplaintId(complaintId) {
        require(bytes(eventType).length > 0, "Event type cannot be empty");
        require(eventHash != bytes32(0), "Event hash cannot be zero");
        
        // Store event hash for later verification
        complaintEventHashes[complaintId].push(eventHash);
        
        // Emit event for off-chain indexing
        emit ComplaintEvent(
            complaintId,
            eventType,
            eventHash,
            block.timestamp
        );
    }
    
    /**
     * @notice Anchor evidence hash on-chain
     * @dev Links IPFS CID with on-chain verification
     * @param complaintId Complaint this evidence relates to
     * @param evidenceHash SHA-256 hash of the evidence file
     */
    function anchorEvidence(
        string memory complaintId,
        bytes32 evidenceHash
    ) external validComplaintId(complaintId) {
        require(evidenceHash != bytes32(0), "Evidence hash cannot be zero");
        require(
            evidenceRegistry[complaintId][evidenceHash] == 0,
            "Evidence already anchored"
        );
        
        // Store evidence with block timestamp
        evidenceRegistry[complaintId][evidenceHash] = block.timestamp;
        
        emit EvidenceAnchored(
            complaintId,
            evidenceHash,
            block.timestamp
        );
    }
    
    /**
     * @notice Set SLA deadline for a complaint
     * @dev Called when complaint is created or assigned
     * @param complaintId Complaint identifier
     * @param deadlineTimestamp Unix timestamp of SLA deadline
     */
    function setSLADeadline(
        string memory complaintId,
        uint256 deadlineTimestamp
    ) external validComplaintId(complaintId) {
        require(
            deadlineTimestamp > block.timestamp,
            "Deadline must be in the future"
        );
        
        slaDeadlines[complaintId] = deadlineTimestamp;
        
        emit SLADeadlineSet(complaintId, deadlineTimestamp);
    }
    
    /**
     * @notice Check and escalate complaint if SLA deadline is breached
     * @dev Can be called by anyone (permissionless escalation)
     * @param complaintId Complaint to check
     * @return success True if escalation occurred
     */
    function checkAndEscalate(string memory complaintId) 
        external 
        validComplaintId(complaintId) 
        returns (bool success) 
    {
        uint256 deadline = slaDeadlines[complaintId];
        
        require(deadline > 0, "No SLA deadline set for this complaint");
        require(!isEscalated[complaintId], "Complaint already escalated");
        
        // Check if deadline has passed
        if (block.timestamp > deadline) {
            isEscalated[complaintId] = true;
            
            emit ComplaintEscalated(
                complaintId,
                deadline,
                block.timestamp
            );
            
            return true;
        }
        
        return false;
    }
    
    /**
     * @notice Batch check multiple complaints for SLA breach
     * @dev Gas-efficient way to check multiple complaints
     * @param complaintIds Array of complaint IDs to check
     * @return escalatedCount Number of complaints escalated
     */
    function batchCheckAndEscalate(string[] memory complaintIds) 
        external 
        returns (uint256 escalatedCount) 
    {
        uint256 count = 0;
        
        for (uint256 i = 0; i < complaintIds.length; i++) {
            string memory complaintId = complaintIds[i];
            uint256 deadline = slaDeadlines[complaintId];
            
            if (deadline > 0 && 
                !isEscalated[complaintId] && 
                block.timestamp > deadline) {
                
                isEscalated[complaintId] = true;
                
                emit ComplaintEscalated(
                    complaintId,
                    deadline,
                    block.timestamp
                );
                
                count++;
            }
        }
        
        return count;
    }
    
    // ============ View Functions ============
    
    /**
     * @notice Verify if an event exists for a complaint
     * @param complaintId Complaint identifier
     * @param eventHash Hash to verify
     * @return exists True if event exists in the log
     */
    function verifyEvent(
        string memory complaintId,
        bytes32 eventHash
    ) external view returns (bool exists) {
        bytes32[] memory events = complaintEventHashes[complaintId];
        
        for (uint256 i = 0; i < events.length; i++) {
            if (events[i] == eventHash) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * @notice Get all event hashes for a complaint
     * @param complaintId Complaint identifier
     * @return Array of event hashes
     */
    function getComplaintEvents(string memory complaintId) 
        external 
        view 
        returns (bytes32[] memory) 
    {
        return complaintEventHashes[complaintId];
    }
    
    /**
     * @notice Verify evidence anchor timestamp
     * @param complaintId Complaint identifier
     * @param evidenceHash Evidence hash to verify
     * @return timestamp Block timestamp when evidence was anchored (0 if not found)
     */
    function verifyEvidenceAnchor(
        string memory complaintId,
        bytes32 evidenceHash
    ) external view returns (uint256 timestamp) {
        return evidenceRegistry[complaintId][evidenceHash];
    }
    
    /**
     * @notice Check if complaint should be escalated
     * @param complaintId Complaint identifier
     * @return shouldEscalate True if past deadline and not yet escalated
     */
    function shouldEscalate(string memory complaintId) 
        external 
        view 
        returns (bool shouldEscalate) 
    {
        uint256 deadline = slaDeadlines[complaintId];
        
        if (deadline == 0) return false;
        if (isEscalated[complaintId]) return false;
        
        return block.timestamp > deadline;
    }
    
    /**
     * @notice Get complaint SLA status
     * @param complaintId Complaint identifier
     * @return deadline SLA deadline timestamp
     * @return escalated Whether complaint is escalated
     * @return timeRemaining Seconds until deadline (0 if past)
     */
    function getSLAStatus(string memory complaintId) 
        external 
        view 
        returns (
            uint256 deadline,
            bool escalated,
            uint256 timeRemaining
        ) 
    {
        deadline = slaDeadlines[complaintId];
        escalated = isEscalated[complaintId];
        
        if (deadline > block.timestamp) {
            timeRemaining = deadline - block.timestamp;
        } else {
            timeRemaining = 0;
        }
        
        return (deadline, escalated, timeRemaining);
    }
    
    // ============ Admin Functions ============
    
    /**
     * @notice Transfer ownership (for contract upgrades)
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "New owner cannot be zero address");
        owner = newOwner;
    }
}
