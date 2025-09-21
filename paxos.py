#!/usr/bin/env python3

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any, Dict
import threading
import time


class MessageType(Enum):
    PREPARE = 'PREPARE'     # Phase 1a: Proposer to Acceptors
    PROMISE = 'PROMISE'     # Phase 1b: Acceptors to Proposer
    ACCEPT = 'ACCEPT'       # Phase 2a: Proposer to Acceptors
    ACCEPTED = 'ACCEPTED'   # Phase 2b: Acceptors to Proposer (and Learners)


@dataclass
class Message:
    msg_type: MessageType
    proposal_id: int
    sender_id: str
    receiver_id: str
    value: Optional[Any] = None
    accepted_proposal_id: Optional[int] = None
    accepted_value: Optional[Any] = None


class Network:
    """Simulates network communication between Paxos nodes"""
    
    def __init__(self):
        self.nodes: Dict[str, 'PaxosNode'] = {}
        self.message_delay = 0.1  # Simulate network delay
        self.message_loss_rate = 0.0  # For future extensions
    
    def add_node(self, node: 'PaxosNode') -> None:
        """Add a node to the network"""
        self.nodes[node.node_id] = node
    
    def send_message(self, message: Message) -> None:
        """Send a message to a specific node"""
        if message.receiver_id in self.nodes:
            # Simulate network delay
            time.sleep(self.message_delay)
            self.nodes[message.receiver_id].receive_message(message)
    
    def broadcast(self, message: Message, exclude: str = None) -> None:
        """Broadcast a message to all nodes except the excluded one"""
        for node_id, node in self.nodes.items():
            if node_id != exclude:
                msg_copy = Message(
                    message.msg_type,
                    message.proposal_id,
                    message.sender_id,
                    node_id,
                    message.value,
                    message.accepted_proposal_id,
                    message.accepted_value
                )
                self.send_message(msg_copy)


class PaxosNode:
    """A Paxos node that can act as proposer, acceptor, and learner"""
    
    def __init__(self, node_id: str, network: Network):
        self.node_id = node_id
        self.network = network
        
        # Proposer state
        self.proposal_id = 0
        self.current_proposal_value = None
        self.promises_received = set()
        self.highest_accepted_id = -1
        self.highest_accepted_value = None
        
        # Acceptor state
        self.promised_proposal_id = -1
        self.accepted_proposal_id = -1
        self.accepted_value = None
        
        # Learner state
        self.learned_values = {}
        self.accept_counts = {}
    
    def propose(self, value: Any) -> None:
        """Start a new proposal as a proposer (Phase 1a)"""
        # Use timestamp to ensure unique proposal IDs across all nodes
        self.proposal_id = int(time.time() * 1000000)  # Microsecond precision
        self.current_proposal_value = value
        self.promises_received.clear()
        
        # Reset highest accepted tracking
        self.highest_accepted_id = -1
        self.highest_accepted_value = None
        
        print(f"📤 Node {self.node_id} proposing value '{value}' with ID {self.proposal_id}")
        
        # Phase 1a: Send PREPARE to all acceptors
        prepare_msg = Message(
            MessageType.PREPARE, 
            self.proposal_id, 
            self.node_id, 
            "broadcast"
        )
        self.network.broadcast(prepare_msg, exclude=self.node_id)
    
    def ReceiveProposeSendPromise(self, message: Message) -> None:
        """Handle PREPARE message as acceptor and send PROMISE (Phase 1b)"""
        print(f"📥 Node {self.node_id} received PREPARE from {message.sender_id} for proposal {message.proposal_id}")
        
        # Check if this proposal ID is higher than any we've promised
        if message.proposal_id > self.promised_proposal_id:
            # Update our promise
            self.promised_proposal_id = message.proposal_id
            
            # Send PROMISE with any previously accepted value
            promise_msg = Message(
                MessageType.PROMISE,
                message.proposal_id,
                self.node_id,
                message.sender_id,
                accepted_proposal_id=self.accepted_proposal_id if self.accepted_proposal_id != -1 else None,
                accepted_value=self.accepted_value
            )
            self.network.send_message(promise_msg)
            print(f"✅ Node {self.node_id} promised to proposal {message.proposal_id}")
        else:
            print(f"❌ Node {self.node_id} ignored proposal {message.proposal_id} (promised to higher: {self.promised_proposal_id})")
    
    def ReceivePromiseSendAccept(self, message: Message) -> None:
        """Handle PROMISE message as proposer and send ACCEPT if majority reached (Phase 2a)"""
        print(f"📥 Node {self.node_id} received PROMISE from {message.sender_id} for proposal {message.proposal_id}")
        
        # Only process promises for our current proposal
        if message.proposal_id == self.proposal_id:
            self.promises_received.add(message.sender_id)
            
            # Check if the promise contains a previously accepted value
            if message.accepted_proposal_id is not None and message.accepted_value is not None:
                # Store the highest accepted proposal we've seen
                if message.accepted_proposal_id > self.highest_accepted_id:
                    self.highest_accepted_id = message.accepted_proposal_id
                    self.highest_accepted_value = message.accepted_value
                    print(f"📝 Node {self.node_id} noted higher accepted proposal {message.accepted_proposal_id} with value '{message.accepted_value}'")
            
            # Check if we have majority of promises
            majority_threshold = len(self.network.nodes) // 2 + 1
            print(f"📊 Node {self.node_id} has {len(self.promises_received)}/{len(self.network.nodes)} promises (need {majority_threshold})")
            
            if len(self.promises_received) >= majority_threshold:
                # Determine value to propose
                if self.highest_accepted_value is not None:
                    # Use the value from the highest accepted proposal
                    value_to_accept = self.highest_accepted_value
                    print(f"🔄 Node {self.node_id} using previously accepted value: '{value_to_accept}'")
                else:
                    # Use our original proposed value
                    value_to_accept = self.current_proposal_value
                    print(f"🆕 Node {self.node_id} using original proposed value: '{value_to_accept}'")
                
                # Phase 2a: Send ACCEPT to all acceptors
                accept_msg = Message(
                    MessageType.ACCEPT,
                    self.proposal_id,
                    self.node_id,
                    "broadcast",
                    value=value_to_accept
                )
                self.network.broadcast(accept_msg, exclude=self.node_id)
                print(f"📤 Node {self.node_id} sent ACCEPT with value: '{value_to_accept}'")
                
                # Clear promises to avoid sending multiple accepts
                self.promises_received.clear()
    
    def ReceiveAcceptSendAccepted(self, message: Message) -> None:
        """Handle ACCEPT message as acceptor and send ACCEPTED (Phase 2b)"""
        print(f"📥 Node {self.node_id} received ACCEPT from {message.sender_id} for proposal {message.proposal_id} with value '{message.value}'")
        
        # Check if we haven't promised to ignore this proposal
        if message.proposal_id >= self.promised_proposal_id:
            # Accept the proposal
            self.accepted_proposal_id = message.proposal_id
            self.accepted_value = message.value
            
            # Send ACCEPTED to proposer and all learners (broadcast to all)
            accepted_msg = Message(
                MessageType.ACCEPTED,
                message.proposal_id,
                self.node_id,
                "broadcast",  # Send to all nodes (proposers and learners)
                value=message.value
            )
            self.network.broadcast(accepted_msg, exclude=self.node_id)
            print(f"✅ Node {self.node_id} accepted proposal {message.proposal_id} with value: '{message.value}'")
        else:
            print(f"❌ Node {self.node_id} ignored ACCEPT for proposal {message.proposal_id} (promised to higher: {self.promised_proposal_id})")
    
    def handle_accepted(self, message: Message) -> None:
        """Handle ACCEPTED message as learner/proposer"""
        print(f"📥 Node {self.node_id} received ACCEPTED from {message.sender_id} for proposal {message.proposal_id} with value '{message.value}'")
        
        # Track accepts for this proposal
        proposal_key = message.proposal_id
        value_key = message.value
        
        if proposal_key not in self.accept_counts:
            self.accept_counts[proposal_key] = {}
        if value_key not in self.accept_counts[proposal_key]:
            self.accept_counts[proposal_key][value_key] = set()
        
        self.accept_counts[proposal_key][value_key].add(message.sender_id)
        
        # Also count our own acceptance if we accepted this proposal
        if (self.accepted_proposal_id == proposal_key and 
            self.accepted_value == value_key):
            self.accept_counts[proposal_key][value_key].add(self.node_id)
        
        # Check if majority reached for this value
        majority_threshold = len(self.network.nodes) // 2 + 1
        accepted_count = len(self.accept_counts[proposal_key][value_key])
        
        print(f"📊 Node {self.node_id} sees {accepted_count}/{len(self.network.nodes)} accepts for proposal {proposal_key} value '{value_key}' (need {majority_threshold})")
        
        if accepted_count >= majority_threshold:
            if proposal_key not in self.learned_values:
                self.learned_values[proposal_key] = value_key
                print(f"🎉 Node {self.node_id} learned CONSENSUS: Proposal {proposal_key} = '{value_key}'")
    
    def receive_message(self, message: Message) -> None:
        """Main message handler with refined method names"""
        try:
            if message.msg_type == MessageType.PREPARE:
                self.ReceiveProposeSendPromise(message)
            elif message.msg_type == MessageType.PROMISE:
                self.ReceivePromiseSendAccept(message)
            elif message.msg_type == MessageType.ACCEPT:
                self.ReceiveAcceptSendAccepted(message)
            elif message.msg_type == MessageType.ACCEPTED:
                self.handle_accepted(message)
            else:
                print(f"❓ Unknown message type: {message.msg_type}")
        except Exception as e:
            print(f"💥 Error in node {self.node_id} handling {message.msg_type}: {e}")


class PaxosSimulation:
    """Main simulation coordinator"""
    
    def __init__(self):
        self.network = Network()
        self.pending_proposals = []
    
    def create_node(self, node_id: str) -> PaxosNode:
        """Create a new node and add it to the network"""
        node = PaxosNode(node_id, self.network)
        self.network.add_node(node)
        return node
    
    def add_proposal(self, node_id: str, value: Any) -> None:
        """Add a proposal to be executed during simulation"""
        if node_id in self.network.nodes:
            self.pending_proposals.append((node_id, value))
    
    def run_simulation(self) -> None:
        """Execute all pending proposals"""
        print("\n" + "="*50)
        print("🚀 Starting Paxos simulation...")
        print("="*50)
        
        # Start proposals with small delays to simulate concurrent proposals
        threads = []
        for i, (node_id, value) in enumerate(self.pending_proposals):
            def propose_after_delay(nid, val, delay):
                time.sleep(delay)
                self.network.nodes[nid].propose(val)
            
            thread = threading.Thread(
                target=propose_after_delay, 
                args=(node_id, value, i * 0.5)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all proposals to complete
        for thread in threads:
            thread.join()
        
        # Give time for consensus to complete
        print("\n⏳ Waiting for consensus to complete...")
        time.sleep(3)
        
        print("\n" + "="*50)
        print("📋 Final Results:")
        print("="*50)
        
        # Show final learned values
        for node_id, node in self.network.nodes.items():
            if node.learned_values:
                print(f"🧠 Node {node_id} learned: {dict(node.learned_values)}")
            else:
                print(f"🤷 Node {node_id} learned nothing")
        
        self.pending_proposals.clear()


def main():
    """Main menu system for the Paxos simulation"""
    sim = PaxosSimulation()
    
    print("🎯 Welcome to Paxos Algorithm Simulation!")
    print("This implementation uses the refined method names:")
    print("  - propose")
    print("  - ReceiveProposeSendPromise") 
    print("  - ReceivePromiseSendAccept")
    print("  - ReceiveAcceptSendAccepted")
    print("  - handle_accepted")
    
    while True:
        print("\n" + "="*40)
        print("🎛️  Paxos Simulation Menu")
        print("="*40)
        print("1. Create node")
        print("2. Add proposal")
        print("3. Run simulation")
        print("4. Show network status")
        print("5. Create test scenario")
        print("6. Exit")
        print("-"*40)
        
        choice = input("Choose an option (1-6): ").strip()
        
        if choice == '1':
            node_id = input("Enter node ID: ").strip()
            if node_id and node_id not in sim.network.nodes:
                sim.create_node(node_id)
                print(f"✅ Node '{node_id}' created successfully")
            else:
                print("❌ Invalid or duplicate node ID")
        
        elif choice == '2':
            if not sim.network.nodes:
                print("❌ Create nodes first!")
                continue
                
            print(f"📋 Available nodes: {list(sim.network.nodes.keys())}")
            node_id = input("Enter proposer node ID: ").strip()
            value = input("Enter proposal value: ").strip()
            
            if node_id in sim.network.nodes and value:
                sim.add_proposal(node_id, value)
                print(f"✅ Proposal '{value}' added for node '{node_id}'")
            else:
                print("❌ Node not found or empty value")
        
        elif choice == '3':
            if sim.pending_proposals:
                sim.run_simulation()
            else:
                print("❌ No pending proposals. Add some proposals first!")
        
        elif choice == '4':
            if not sim.network.nodes:
                print("❌ No nodes in network")
            else:
                print(f"🌐 Network has {len(sim.network.nodes)} nodes:")
                for node_id, node in sim.network.nodes.items():
                    learned = list(node.learned_values.values()) if node.learned_values else []
                    print(f"  📍 {node_id}: learned values = {learned}")
        
        elif choice == '5':
            # Create a test scenario with 3 nodes and competing proposals
            print("🧪 Creating test scenario...")
            
            # Clear existing network
            sim = PaxosSimulation()
            
            # Create 3 nodes (minimum for majority)
            for i in range(3):
                sim.create_node(f"node{i}")
            
            # Add competing proposals
            sim.add_proposal("node0", "value_A")
            sim.add_proposal("node1", "value_B") 
            sim.add_proposal("node2", "value_C")
            
            print("✅ Test scenario created:")
            print("  - 3 nodes: node0, node1, node2")
            print("  - 3 competing proposals: value_A, value_B, value_C")
            print("  - Use option 3 to run the simulation")
        
        elif choice == '6':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-6.")


if __name__ == "__main__":
    main()