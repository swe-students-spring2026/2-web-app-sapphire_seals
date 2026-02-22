import os
from datetime import datetime
import requests
import json

''' 
DB STRUCTURE:

halls:
    # check (https://apiv4.dineoncampus.com/sites/5cab70a48e45bf099f4a9970/locations-public?for_menus=true).standaloneLocations
    _id = id = locationId: str
    name: str
    slug: str
    certifiedKindnessKitchen: bool
    greenRestaurant: bool
    hasLocalBrands: bool
    hasNationalBrands: bool
    mobileOrderingLabel: str | None
    mobileOrderingUrl: str | None
    sortOrder: int

menus:
    # Search via locationId recommended.
    _id = id: str (period id)
    locationId: str (foreign key to halls)
    name = periodName: str (Breakfast, Lunch, Dinner, etc.)
    slug: null
    categories: category[]
        category:
            id: str (category id)
            name: str
            items: food[]
            sortOrder: int

foods:
    _id = id: str (food id)
    calories: int
    customAllergens: str[]
    desc: str (description)
    filters: filter[]
        filter:
            id: str (filter id)
            name: str
            icon: bool
            remoteFileName: str | None (Do not rely on this)
    ingredients: str
    mrn: int
    mrnFull: str
    name: str
    nutrients: nutrient[]
        nutrient:
            id: null
            name: str
            value: str
            uom: str
            valueNumeric: str
    portion: str
    qty: str | None
    rev: str | None
    sortOrder: int
    webtritionId: str | None
    foodEdges: [hallLocationId, periodId]
    averageScore: float
    ratings: rating[]
        rating:
            user_id: str (foreign key to users)
            score: float
            content: str
            createdAt: datetime
            updatedAt: datetime

users:
    _id = id: str (user id)
    name: str
    email: str
    password: str
    netId: str


'''

def get_halls():
    data = requests.get("https://apiv4.dineoncampus.com/sites/5cab70a48e45bf099f4a9970/locations-public?for_menus=true").json()
    data = data["standaloneLocations"]
    for i in range(len(data)):
        data[i]["_id"] = data[i]["id"]
    return data

def today(): # Macro
    return datetime.now().strftime("%Y-%m-%d")

def get_periods(id): 
    # Period ids for breakfast, lunch, dinner, etc, to get the specific menu.
    # Refreshes every second... omg
    return requests.get(f"https://apiv4.dineoncampus.com/locations/{id}/periods/?date={today()}").json()

def get_menu(id): 
    # Get the menu for all periods of a specific hall. 
    # Seems like there's no way to get a "global" menu.
    date = today()
    periods = get_periods(id)
    menus = []
    for period in periods["periods"]:
        menu = requests.get(f"https://apiv4.dineoncampus.com/locations/{id}/menu?date={date}&period={period["id"]}").json()["period"]
        menus.append(menu)
    return menus

def datadump():
    halls = get_halls()
    open("halls.json", "w").write(json.dumps(halls))
    print("Halls dumped")
    menus = []
    for hall in halls:
        print(f"Getting menus for {hall['name']}")
        hall_menus = get_menu(hall["id"])
        for menu in hall_menus:
            menu["locationId"] = hall["id"]
            menu["_id"] = menu["id"]
            menu["periodName"] = menu["name"]
            menus.append(menu)
    open("menus.json", "w").write(json.dumps(menus))
    print("Menus dumped")
    foods = []
    tags = []
    tags_dedup = {}
    for menu in menus:
        for category in menu["categories"]:
            print(f"Getting foods for {category['name']}")
            for food in category["items"]:
                food["foodEdges"] = [menu["locationId"], menu["id"]]
                food["averageScore"] = 0
                foods.append(food)
                for filter in food["filters"]:
                    if filter["id"] not in tags_dedup:
                        tags_dedup[filter["id"]] = True
                        tags.append(filter)
    print("Foods dumped")
    open("foods.json", "w").write(json.dumps(foods))
    open("tags.json", "w").write(json.dumps(tags))

if __name__ == "__main__":
    # This is gonna take a while...
    datadump()