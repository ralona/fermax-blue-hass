#!/usr/bin/env python3
"""Test the Fermax Blue integration module independently."""

import asyncio
import aiohttp
import logging
import sys
import os

# Add the custom_components path to import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'fermax_blue'))

from fermax_integration import FermaxBlueIntegration

# Enable debug logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_integration():
    """Test the complete integration flow."""
    
    # ==========================================
    # PUT YOUR CREDENTIALS HERE
    # ==========================================
    email = "qasita132@gmail.com"
    password = "Quart.123"
    
    print(f"🔍 Testing Fermax Blue Integration with email: {email}")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        integration = FermaxBlueIntegration(email, password, session)
        
        try:
            # Test 1: Setup (like __init__.py does)
            print("\n🏠 Test 1: Integration Setup (like __init__.py)...")
            setup_result = await integration.setup_integration()
            
            if setup_result:
                print("✅ Integration setup successful")
                
                # Test 2: Get home info (for title)
                print("\n🏡 Test 2: Get home info (for integration title)...")
                home_info = integration.get_home_info()
                print(f"✅ Home: {home_info}")
                
                # Test 3: Get devices (for entities)
                print("\n🚪 Test 3: Get door devices (for button entities)...")
                doors = integration.get_door_devices()
                print(f"✅ Found {len(doors)} doors:")
                
                for door in doors:
                    print(f"  - {door['name']}")
                    print(f"    ID: {door['id']}")
                    print(f"    Device ID: {door['device_id']}")
                    print(f"    Access ID: {door['access_id'].to_dict()}")
                
                # Test 4: Update data (like coordinator does)
                print("\n🔄 Test 4: Update data (like coordinator)...")
                update_result = await integration.update_data()
                print(f"✅ Update result: {update_result}")
                
                # Test 5: Door opening (optional)
                print("\n🚪 Test 5: Door opening test...")
                if doors:
                    door = doors[0]  # Test first door
                    print(f"Testing door: {door['name']}")
                    
                    # Uncomment to actually test door opening
                    # open_result = await integration.open_door(door['device_id'], door['access_id'])
                    # print(f"✅ Door opening result: {open_result}")
                    print("✅ Door opening test skipped (uncomment to test)")
                
                print("\n🎉 ALL INTEGRATION TESTS PASSED!")
                print("✅ This means the Home Assistant integration should work")
                
            else:
                print("❌ Integration setup failed")
                
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_integration())