import httpx
import asyncio
import json

class StellariumBridge:
    def __init__(self, host="localhost", port=8090):
        self.base_url = f"http://{host}:{port}/api"

    async def get_status(self):
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{self.base_url}/main/status")
                return resp.json()
            except Exception as e:
                return {"error": f"Stellarium Connection Failed: {str(e)}"}

    async def set_location(self, lat, lon, altitude=0, name="Mythic_POV"):
        """Sets observer location in Stellarium."""
        payload = {
            "latitude": lat,
            "longitude": lon,
            "altitude": altitude,
            "name": name
        }
        async with httpx.AsyncClient() as client:
            return await client.post(f"{self.base_url}/location/setlocationfields", data=payload)

    async def set_time(self, jday):
        """Sets simulation time in Julian Day."""
        payload = {"time": jday}
        async with httpx.AsyncClient() as client:
            return await client.post(f"{self.base_url}/main/time", data=payload)

    async def focus_object(self, name):
        """Focuses and zooms on a specific celestial object."""
        payload = {"target": name}
        async with httpx.AsyncClient() as client:
            return await client.post(f"{self.base_url}/main/focus", data=payload)

    async def toggle_view_option(self, option, state=True):
        """Toggles view options like constellation lines, labels, etc."""
        # Options: constellations, constellation_labels, grids, etc.
        payload = {option: "true" if state else "false"}
        async with httpx.AsyncClient() as client:
            return await client.post(f"{self.base_url}/view/setviewoptions", data=payload)

if __name__ == "__main__":
    # Test script for the bridge
    bridge = StellariumBridge()
    print("Stellarium Bridge Logic Ready.")
