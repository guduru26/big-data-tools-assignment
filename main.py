from datetime import datetime
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import redis
import requests

class DataFetch:
    def __init__(self, url):
        """
        Initializes a DataFetch object with the given URL.

        Args:
            url (str): The URL to fetch data from.
        """
        self.url = url

    def fetch(self, method="GET"):
        """
        Fetches data from the specified URL using the given HTTP method.

        Args:
            method (str, optional): The HTTP method to use for the request. Defaults to "GET".

        Returns:
            dict: The JSON response from the request, or an empty dictionary if an error occurred.
        """
        try:
            response = requests.request(method, self.url)
            response.raise_for_status()  # Raises stored HTTPError, if one occurred.
            return response.json()
        except requests.RequestException as e:
            print(f"Request error: {e}")
            return {}


class RedisJson:
    """
    A class for interacting with Redis JSON data.

    Args:
        host (str): The Redis server host. Default is "localhost".
        port (int): The Redis server port. Default is 6379.
        db (int): The Redis database index. Default is 0.

    Attributes:
        client (redis.Redis): The Redis client instance.

    """

    def __init__(self, host="localhost", port=6379, db=0):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def set(self, key, value):
        """
        Set a JSON value in Redis.

        Args:
            key (str): The key to set.
            value (str): The JSON value to set.

        """
        try:
            self.client.json().set(key, "$", value)
        except Exception as e:
            print(f"Redis set error: {e}")

    def get(self, key):
        """
        Get a JSON value from Redis.

        Args:
            key (str): The key to get.

        Returns:
            str: The JSON value associated with the key, or an empty dictionary if not found.

        """
        try:
            return self.client.json().get(key)
        except Exception as e:
            print(f"Redis get error: {e}")
            return {}


class ProcessData:
    """
    A class that provides methods for processing and plotting data related to Bitcoin prices.
    """

    @staticmethod
    def validate_data(data):
        """
        Validates the data structure.

        Args:
            data (dict): The data to be validated.

        Returns:
            bool: True if the data structure is valid, False otherwise.
        """
        # Implement basic validation of data structure
        return "prices" in data

    @staticmethod
    def plot_line_chart(data):
        """
        Plots a line chart of Bitcoin prices over time.

        Args:
            data (dict): The data containing Bitcoin prices.

        Raises:
            ValueError: If the data structure is invalid.

        Returns:
            None
        """
        if not ProcessData.validate_data(data):
            raise ValueError("Invalid data format for plotting")
        
        timestamps = [datetime.fromtimestamp(x[0] / 1000) for x in data["prices"]]
        prices = [x[1] for x in data["prices"]]

        plt.figure(figsize=(16, 9))
        plt.plot_date(timestamps, prices, "-")

        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y/%m/%d"))
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))
        plt.gcf().autofmt_xdate()

        plt.title("Bitcoin Price Over Time")
        plt.ylabel("Price in $")
        plt.grid(True)
        plt.savefig("line_chart.png")  
        plt.close() 

    @staticmethod
    def plot_histogram(data):
        if not ProcessData.validate_data(data):
            print("Invalid data format for plotting")
            return
        
        prices = [x[1] for x in data["prices"]]
        price_changes = [b - a for a, b in zip(prices[:-1], prices[1:])]

        plt.figure(figsize=(9, 4))
        plt.hist(price_changes, bins=50, alpha=0.5, color="g")
        plt.title("Distribution of Bitcoin Price Changes")
        plt.xlabel("Price Change")
        plt.savefig("histogram.png")
        plt.close()

    @staticmethod
    def plot_scatter(data):
        if not ProcessData.validate_data(data):
            print("Invalid data format for plotting")
            return
        
        prices = [x[1] for x in data["prices"]]
        price_changes = [b - a for a, b in zip(prices[:-1], prices[1:])]
        timestamps = [datetime.fromtimestamp(x[0] / 1000) for x in data["prices"][1:]]

        plt.figure(figsize=(9, 4))
        plt.scatter(timestamps, price_changes, alpha=0.5, color="r")
        plt.gcf().autofmt_xdate()
        plt.title("Bitcoin Price Changes Over Time")
        plt.xlabel("Date")
        plt.ylabel("Price Change")
        plt.savefig("scatter_plot.png")
        plt.close()


class DataAggregator:
    """
    A class that provides methods for calculating average, maximum, minimum prices, and price change from data.

    Methods:
    - calculate_average_price(data): Calculates the average price from the given data.
    - find_max_price(data): Finds the maximum price from the given data.
    - find_min_price(data): Finds the minimum price from the given data.
    - calculate_price_change(data): Calculates the price change from the given data.
    """
    @staticmethod
    def calculate_average_price(data):
        if not data or "prices" not in data:
            return None
        prices = [x[1] for x in data["prices"]]
        average_price = sum(prices) / len(prices) if prices else None
        return average_price

    @staticmethod
    def find_max_price(data):
        if not data or "prices" not in data:
            return None
        prices = [x[1] for x in data["prices"]]
        max_price = max(prices) if prices else None
        return max_price

    @staticmethod
    def find_min_price(data):
        if not data or "prices" not in data:
            return None
        prices = [x[1] for x in data["prices"]]
        min_price = min(prices) if prices else None
        return min_price

    @staticmethod
    def calculate_price_change(data):
        if not data or "prices" not in data:
            return None
        prices = [x[1] for x in data["prices"]]
        if len(prices) < 2:
            return None
        price_change = prices[-1] - prices[0]
        return price_change


if __name__ == "__main__":
    API_URL = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=5"

    fetcher = DataFetch(API_URL)
    data = fetcher.fetch()

    if data:
        redisClient = RedisJson()
        redisClient.set("bitcoin_data", data)

        stored_data = redisClient.get("bitcoin_data")
        if stored_data:
            processor = ProcessData()
            processor.plot_line_chart(stored_data)
            processor.plot_histogram(stored_data)
            processor.plot_scatter(stored_data)

            aggregator = DataAggregator()
            average_price = aggregator.calculate_average_price(stored_data)
            max_price = aggregator.find_max_price(stored_data)
            min_price = aggregator.find_min_price(stored_data)
            price_change = aggregator.calculate_price_change(stored_data)

            print(f"Average Price: {average_price}")
            print(f"Maximum Price: {max_price}")
            print(f"Minimum Price: {min_price}")
            print(f"Price Change: {price_change}")
        else:
            print("Failed to retrieve data from Redis.")
    else:
        print("Failed to fetch data from API.")
