"""
End-to-end test suite for multi-tenant client onboarding flow.
Tests: signup → config storage → message routing → lead capture → notifications.
"""

import os
import sys

# Load .env file BEFORE any project imports so ANTHROPIC_API_KEY is available
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from test_e2e_setup import (
    TestClientFixture,
    TestDatabase,
    MultiTenantBotRouter,
    TestNotificationCapture,
)


def test_client_signup_and_config_storage():
    """Test 1: Client signs up and config is stored correctly."""
    print("\n" + "=" * 70)
    print("TEST 1: Client Signup and Config Storage")
    print("=" * 70)

    db = TestDatabase()
    client = TestClientFixture("ABC Plumbing", "John Smith", "+15551234567")

    # Simulate signup
    db.create_account(client.account_id, "ABC Plumbing", "John Smith")
    db.store_business_profile(client.account_id, client.business_config)
    db.store_channel(client.account_id, "whatsapp:+14155238886")

    # Verify
    stored_config = db.get_business_profile(client.account_id)
    assert stored_config is not None, "Config not stored"
    assert stored_config["name"] == "ABC Plumbing", "Business name mismatch"
    assert stored_config["owner_name"] == "John Smith", "Owner name mismatch"
    assert stored_config["owner_notify_number"] == "+15551234567", "Owner phone mismatch"

    print(f"✅ Account created: {client.account_id}")
    print(f"✅ Business config stored: {stored_config['name']}")
    print(f"✅ Owner notification number: {stored_config['owner_notify_number']}")
    return True


def test_message_routing_to_correct_client():
    """Test 2: Messages route to the correct client's bot."""
    print("\n" + "=" * 70)
    print("TEST 2: Message Routing to Correct Client")
    print("=" * 70)

    db = TestDatabase()
    router = MultiTenantBotRouter(db)

    # Create two test clients
    client1 = TestClientFixture("ABC Plumbing", "John", "+15551111111")
    client2 = TestClientFixture("XYZ Electric", "Jane", "+15552222222")

    # Store both clients
    db.store_business_profile(client1.account_id, client1.business_config)
    db.store_business_profile(client2.account_id, client2.business_config)

    # Send message to client 1
    reply1 = router.send_message(client1.account_id, "hi")
    assert "ABC Plumbing" in reply1, f"Client 1 bot didn't mention their business: {reply1}"

    # Send message to client 2
    reply2 = router.send_message(client2.account_id, "hi")
    assert "XYZ Electric" in reply2, f"Client 2 bot didn't mention their business: {reply2}"

    print(f"✅ Client 1 ({client1.account_id}): {reply1[:60]}...")
    print(f"✅ Client 2 ({client2.account_id}): {reply2[:60]}...")
    return True


def test_lead_capture_attribution():
    """Test 3: Leads are captured and attributed to correct client."""
    print("\n" + "=" * 70)
    print("TEST 3: Lead Capture and Attribution")
    print("=" * 70)

    db = TestDatabase()
    router = MultiTenantBotRouter(db)
    client = TestClientFixture("ABC Plumbing", "John", "+15551234567")

    db.store_business_profile(client.account_id, client.business_config)

    # Simulate a lead capture conversation
    messages = [
        "hi",
        "my drain is clogged",
        "tomorrow at 9am",
        "it's sarah, 720-555-4321",
    ]

    for msg in messages:
        reply = router.send_message(client.account_id, msg)
        print(f"  Customer: {msg}")
        print(f"  Bot: {reply[:70]}...")

    # Verify lead was captured and attributed
    leads = db.get_leads(client.account_id)
    assert len(leads) > 0, "No leads captured"
    assert leads[0]["name"].lower() == "sarah", f"Lead name mismatch: {leads[0]}"
    assert "drain" in leads[0]["service"].lower(), f"Service mismatch: {leads[0]}"

    print(f"\n✅ Lead captured: {leads[0]}")
    return True


def test_owner_notification_routing():
    """Test 4: Owner notifications go to correct phone number."""
    print("\n" + "=" * 70)
    print("TEST 4: Owner Notification Routing")
    print("=" * 70)

    db = TestDatabase()
    notifications = TestNotificationCapture()
    client = TestClientFixture("ABC Plumbing", "John", "+15551234567")

    db.store_business_profile(client.account_id, client.business_config)

    # Simulate lead capture
    lead = {
        "name": "Sarah",
        "service": "drain cleaning",
        "time": "tomorrow 9am",
        "phone": "720-555-4321",
    }

    # Capture notification
    notifications.capture_notification(
        client.account_id,
        lead,
        client.business_config,
    )

    # Verify notification
    notifs = notifications.get_notifications_for_account(client.account_id)
    assert len(notifs) > 0, "No notifications captured"
    assert notifs[0]["business"]["owner_notify_number"] == "+15551234567"

    print(f"✅ Notification captured for: {client.business_config['name']}")
    print(f"✅ Owner phone: {notifs[0]['business']['owner_notify_number']}")
    print(f"✅ Lead: {notifs[0]['lead']}")
    return True


def test_multiple_clients_isolation():
    """Test 5: Multiple clients don't interfere with each other."""
    print("\n" + "=" * 70)
    print("TEST 5: Multi-Client Isolation")
    print("=" * 70)

    db = TestDatabase()
    router = MultiTenantBotRouter(db)

    # Create 3 clients
    clients = [
        TestClientFixture("ABC Plumbing", "John", "+15551111111"),
        TestClientFixture("XYZ Electric", "Jane", "+15552222222"),
        TestClientFixture("DEF HVAC", "Bob", "+15553333333"),
    ]

    for client in clients:
        db.store_business_profile(client.account_id, client.business_config)

    # Realistic service-specific conversations per client so Claude reliably captures leads
    conversations = [
        [
            "hi",
            "my kitchen sink is leaking badly",
            "tomorrow morning around 9am works",
            "it's customer0, 720-555-0000",
        ],
        [
            "hi",
            "i need an outlet installed in my garage",
            "this saturday afternoon if possible",
            "it's customer1, 720-555-1111",
        ],
        [
            "hi",
            "my AC stopped blowing cold air",
            "any time wednesday works for me",
            "it's customer2, 720-555-2222",
        ],
    ]

    # Send leads to each client
    for i, client in enumerate(clients):
        for msg in conversations[i]:
            router.send_message(client.account_id, msg)

    # Verify isolation
    for i, client in enumerate(clients):
        leads = db.get_leads(client.account_id)
        assert len(leads) > 0, f"Client {i} has no leads"
        assert f"customer{i}" in leads[0]["name"].lower(), f"Client {i} lead mismatch: {leads[0]}"

    print(f"✅ All {len(clients)} clients isolated correctly")
    for client in clients:
        leads = db.get_leads(client.account_id)
        print(f"   {client.business_config['name']}: {len(leads)} lead(s)")
    return True


def run_all_tests():
    """Run all end-to-end tests."""
    print("\n" + "█" * 70)
    print("  MULTI-TENANT BOT E2E TEST SUITE")
    print("█" * 70)

    tests = [
        ("Signup & Config Storage", test_client_signup_and_config_storage),
        ("Message Routing", test_message_routing_to_correct_client),
        ("Lead Capture Attribution", test_lead_capture_attribution),
        ("Owner Notifications", test_owner_notification_routing),
        ("Multi-Client Isolation", test_multiple_clients_isolation),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            if test_fn():
                passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1

    print("\n" + "█" * 70)
    print(f"  RESULTS: {passed} passed, {failed} failed")
    print("█" * 70 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

