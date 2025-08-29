import requests
import json

# Common headers for all APIs (replace values as per your credentials)
HEADERS_SEARCH = {
    "Content-Type": "application/json",
    "Authorization": "Basic YWFjbTNreGVldjNsbTdkNnA5NTRhZGtrbzAybTh1dzRldDEydXAycDduNjhraHpzeDU=",
    "Cookie": "JSESSIONID=5C6F01C47C06D84F73A436841AFFC24E; _KAPTURECRM_SESSION="
}

HEADERS_REGISTER = {
    "Content-Type": "application/json",
    "Authorization": "Basic enU2dDc2cjlkY20zMWU3dWsxbmR4cjRjeTJ5ZzR4cDdrYzdibzl4amxoaXJqYmM4bV"
}

HEADERS_ORDER = {
    "Content-Type": "application/json",
    "Authorization": "Basic aDd3MWY0dno0MGsxaTRxb3phZnR6N3A4ZHNhdzhyOTZ5aG84a3N6OXhuemwx"
}

def search_customer(phone="9981342605", customer_id=None, email=None, kapture_customer_id=None):
    url = "https://faber.kapturecrm.com/search-customer-by-customer-id.html"
    payload = [{
        "kapture_customer_id": kapture_customer_id or "",
        "customer_id": customer_id or "",
        "email_id": email or "",
        "phone": phone or ""
    }]
    response = requests.post(url, headers=HEADERS_SEARCH, data=json.dumps(payload))
    print("Search Customer Response:", response)
    customer = response.json()
    if customer['status']=="success":
        details = customer["Customer Details"]
        processed_data = {
            "customer_id": details["id"],
            "name": details["name"],
            "address":details["address"],
            "pinCode":details["pinCode"],
            "phone":details["contacts"][0]["phone"],
        }
        return {"status_code":200,"status": "success", "data": processed_data}
    else:
        return {"status_code":404,"status": "error", "message": "Customer not found."}
    
def register_customer(customer_data):
    """
    customer_data: dict with keys:
    customer_name, phone, country, state, city, address, pincode, contact_person_name, contact_person_phone
    """
    url = "https://faber.kapturecrm.com/add-update-enquiry"
    # response = requests.post(url, headers=HEADERS_REGISTER, json=customer_data)
    # return response.json()
    print("Registering Customer:", customer_data)
    return {"status_code":200,"status": "success", "message": "Customer registration simulated."}

def validate_pincode(pincode):
    url = f"https://faber.kapturecrm.com/ms/mobile/location/api/v1/noauth/pincode-mapping?pincode={pincode}"
    headers = {"Content-Type": "text/plain"}
    response = requests.get(url, headers=headers)
    print("Pincode Validation Response:", response)
    return response.json()

def create_order(order_data):
    """
    order_data: dict containing contact_info, customer_info, enquiry_info, order_info, product_details
    """
    url = "https://faber.kapturecrm.com/ms/customer/order/api/v1/add-update"
    # response = requests.post(url, headers=HEADERS_ORDER, json=order_data)
    # return response.json()
    print("Order Data:", order_data)
    return {"status_code":200,"status": "success", "message": "Order creation simulated.", "order_id": "ORD123456"}

def generate_ticket(ticket_data):
    url = "https://faber.kapturecrm.com/add-update-enquiry"
    print("Ticket Data:", ticket_data)
    return {"status_code":200,"status": "success", "message": "Ticket generation simulated.", "ticket_id": "TICK123456"}
    # response = requests.post(url, headers=HEADERS_REGISTER, json=ticket_data)
    # return response.json()

# Example usage:
if __name__ == "__main__":
    # Search customer
    customer = search_customer(phone="9981342605")
    # if customer['status']=="success":
    #     details = customer[0]["Customer Details"]
    #     processed_data = {
    #         "customer_id": details["id"],
    #         "name": details["name"],
    #         "address":details["address"],
    #         "pinCode":details["pinCode"],
    #         "phone":details["contacts"][0]["phone"],
    #     }
    print(customer)

    # Validate PIN
    # pin_info = validate_pincode("380009")
    # print(pin_info)
