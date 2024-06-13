import unittest
import requests
import jsonschema
from jsonschema import validate

BASE_URL = "https://interviews-api.beefreeagro.com/api/v1"

# Define schemas
drone_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "drone_code": {"type": "string"},
            "name": {"type": "string"},
            "range": {"type": "number"},
            "release_date": {"type": "string", "format": "date-time"},
            "cameras": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "megapixels": {"type": "number"},
                        "name": {"type": "string"},
                        "type": {"type": "string"}
                    },
                    "required": ["megapixels", "name", "type"]
                }
            }
        },
        "required": ["drone_code", "name", "range", "release_date"]
    }
}

validation_error_schema = {
    "type": "object",
    "properties": {
        "detail": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "loc": {
                        "type": "array",
                        "items": {
                            "anyOf": [
                                {"type": "string"},
                                {"type": "integer"}
                            ]
                        }
                    },
                    "msg": {"type": "string"},
                    "type": {"type": "string"}
                },
                "required": ["loc", "msg", "type"]
            }
        }
    },
    "required": ["detail"]
}

# Function to validate JSON against a schema
def validate_json(data, schema):
    try:
        validate(instance=data, schema=schema)
        print("JSON data is valid.")
    except jsonschema.exceptions.ValidationError as err:
        print("JSON data is invalid.")
        print(err)

class APITestCase(unittest.TestCase):

    def test_get_health_status(self):
        response = requests.get(f"{BASE_URL}/health")
        self.assertEqual(response.status_code, 200)
        print("Response Headers:", response.headers)
        print("Response Text:", response.text)
        
        if response.headers.get('Content-Type') == 'application/json':
            response_json = response.json()
            print(response_json)  
            self.assertIn("health", response_json)
            self.assertEqual(response_json["health"], "ok")
        else:
            print("Received non-JSON response")
            self.assertTrue("swagger-ui" in response.text, "Expected Swagger UI page content")

    def test_trigger_division_by_zero_error(self):
        response = requests.get(f"{BASE_URL}/sentry")
        print("Response Status Code:", response.status_code)
        print("Response Headers:", response.headers)
        print("Response Text:", response.text)
        
        self.assertEqual(response.status_code, 500, f"Expected status code 500, but got {response.status_code}")
        
        # Check if the content type is JSON
        content_type = response.headers.get('Content-Type')
        if content_type and 'application/json' in content_type:
            try:
                response_json = response.json()
                print(response_json)
                self.assertIsInstance(response_json, dict)
            except ValueError:
                self.fail("Expected JSON response but could not parse JSON")
        else:
            # Check for non-JSON response with specific error text
            self.assertTrue(response.text.strip() == "", "Expected error message in the response")



    def test_get_drones(self):
        response = requests.get(f"{BASE_URL}/drones")
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        print(response_json) 
        self.assertIsInstance(response_json, list)
        for drone in response_json:
            validate_json(drone, drone_schema)

    def test_get_drone_by_model_code(self):
        drone_code = "M3T"
        response = requests.get(f"{BASE_URL}/drones/{drone_code}")
        self.assertEqual(response.status_code, 200)
        drone_data = response.json()
        print(drone_data) 
        self.assertIn("drone_code", drone_data)
        self.assertEqual(drone_data["drone_code"], drone_code)
        validate_json(drone_data, drone_schema)

    def test_get_drone_image(self):
        drone_code = "M3T"
        response = requests.get(f"{BASE_URL}/drones/{drone_code}/image")
        self.assertEqual(response.status_code, 200)
        print("Response Headers:", response.headers)
        self.assertTrue(response.headers['Content-Type'].startswith('image/'), "Response is not an image")
        with open(f"{drone_code}_image.png", "wb") as file:
            file.write(response.content)
        print(f"Image saved as {drone_code}_image.png")

    def test_invalid_drone_code(self):
        drone_code = "gggg"
        response = requests.get(f"{BASE_URL}/drones/{drone_code}")
        self.assertEqual(response.status_code, 404)
        error_data = response.json()
        print(error_data) 

if __name__ == '__main__':
    unittest.main()
