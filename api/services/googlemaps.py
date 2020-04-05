import googlemaps

PUBLIC_KEY = 'AIzaSyCpP0ntj7-duoKslNF8XJTMiAtAc5BZfrA'
gmaps = googlemaps.Client(key=PUBLIC_KEY)


geocode_result = gmaps.geocode('1600 Amphitheatre Parkway, Mountain View, CA')
print("geocode_result#", geocode_result)