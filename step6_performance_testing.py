"""
STEP 6: PERFORMANCE & LOAD TESTING
===================================
Test your recommendation API for performance and reliability
"""

import requests
import time
import statistics
import concurrent.futures
from datetime import datetime
import json
import matplotlib.pyplot as plt

class RecommendationAPITester:
    """
    Performance testing for recommendation API
    """
    
    def __init__(self, api_base_url='http://localhost:5000'):
        self.api_base_url = api_base_url
        self.results = []
        
    def test_health_check(self):
        """Test 1: Basic health check"""
        print("\n" + "="*60)
        print("TEST 1: Health Check")
        print("="*60)
        
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    def test_response_time(self, endpoint, params=None, iterations=100):
        """Test 2: Measure response time"""
        print("\n" + "="*60)
        print(f"TEST 2: Response Time - {endpoint}")
        print("="*60)
        
        response_times = []
        
        for i in range(iterations):
            start_time = time.time()
            try:
                response = requests.get(
                    f"{self.api_base_url}{endpoint}",
                    params=params,
                    timeout=10
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    response_times.append((end_time - start_time) * 1000)  # Convert to ms
                else:
                    print(f"⚠ Request {i+1} failed with status {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Request {i+1} error: {e}")
        
        if response_times:
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
            p99_time = sorted(response_times)[int(len(response_times) * 0.99)]
            
            print(f"\n📊 Response Time Statistics ({iterations} requests):")
            print(f"  Average:    {avg_time:.2f} ms")
            print(f"  Median:     {median_time:.2f} ms")
            print(f"  Min:        {min_time:.2f} ms")
            print(f"  Max:        {max_time:.2f} ms")
            print(f"  95th %ile:  {p95_time:.2f} ms")
            print(f"  99th %ile:  {p99_time:.2f} ms")
            
            # Check if meeting performance requirements
            if p95_time < 200:
                print("\n✓ PASS: 95th percentile < 200ms target")
            else:
                print("\n✗ FAIL: 95th percentile exceeds 200ms target")
            
            return {
                'avg': avg_time,
                'median': median_time,
                'p95': p95_time,
                'p99': p99_time,
                'times': response_times
            }
        
        return None
    
    def test_concurrent_requests(self, endpoint, num_concurrent=50, total_requests=200):
        """Test 3: Concurrent request handling"""
        print("\n" + "="*60)
        print(f"TEST 3: Concurrent Load - {num_concurrent} concurrent users")
        print("="*60)
        
        def make_request():
            start_time = time.time()
            try:
                response = requests.get(f"{self.api_base_url}{endpoint}", timeout=30)
                end_time = time.time()
                return {
                    'success': response.status_code == 200,
                    'time': (end_time - start_time) * 1000,
                    'status': response.status_code
                }
            except Exception as e:
                return {
                    'success': False,
                    'time': None,
                    'error': str(e)
                }
        
        results = []
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(make_request) for _ in range(total_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        
        # Analyze results
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        success_rate = (len(successful) / total_requests) * 100
        total_time = end_time - start_time
        throughput = total_requests / total_time
        
        if successful:
            response_times = [r['time'] for r in successful]
            avg_response = statistics.mean(response_times)
        else:
            avg_response = 0
        
        print(f"\n📊 Concurrent Load Test Results:")
        print(f"  Total Requests:     {total_requests}")
        print(f"  Concurrent Users:   {num_concurrent}")
        print(f"  Total Time:         {total_time:.2f} seconds")
        print(f"  Throughput:         {throughput:.2f} requests/second")
        print(f"  Success Rate:       {success_rate:.2f}%")
        print(f"  Successful:         {len(successful)}")
        print(f"  Failed:             {len(failed)}")
        print(f"  Avg Response Time:  {avg_response:.2f} ms")
        
        if success_rate >= 99.5:
            print("\n✓ PASS: Success rate >= 99.5%")
        else:
            print("\n✗ FAIL: Success rate below 99.5%")
        
        return {
            'success_rate': success_rate,
            'throughput': throughput,
            'avg_response': avg_response
        }
    
    def test_different_endpoints(self):
        """Test 4: Test all API endpoints"""
        print("\n" + "="*60)
        print("TEST 4: All Endpoints Performance")
        print("="*60)
        
        endpoints = [
            {
                'name': 'User Recommendations',
                'endpoint': '/api/v1/recommendations/user/1',
                'params': {'n': 10}
            },
            {
                'name': 'Similar Items',
                'endpoint': '/api/v1/recommendations/similar/1',
                'params': {'n': 10}
            },
            {
                'name': 'Popular Items',
                'endpoint': '/api/v1/recommendations/popular',
                'params': {'n': 10}
            }
        ]
        
        results = {}
        
        for endpoint_config in endpoints:
            print(f"\n→ Testing: {endpoint_config['name']}")
            result = self.test_response_time(
                endpoint_config['endpoint'],
                endpoint_config['params'],
                iterations=50
            )
            results[endpoint_config['name']] = result
        
        return results
    
    def test_cache_effectiveness(self, endpoint, iterations=100):
        """Test 5: Cache hit rate and performance"""
        print("\n" + "="*60)
        print("TEST 5: Cache Effectiveness")
        print("="*60)
        
        # Test same request multiple times
        first_request_time = None
        cached_times = []
        
        for i in range(iterations):
            start_time = time.time()
            response = requests.get(f"{self.api_base_url}{endpoint}")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            
            if i == 0:
                first_request_time = response_time
                print(f"First request (cold): {first_request_time:.2f} ms")
            else:
                cached_times.append(response_time)
        
        if cached_times:
            avg_cached = statistics.mean(cached_times)
            speedup = first_request_time / avg_cached
            
            print(f"\n📊 Cache Performance:")
            print(f"  First request (cold):      {first_request_time:.2f} ms")
            print(f"  Avg cached request:        {avg_cached:.2f} ms")
            print(f"  Cache speedup:             {speedup:.2f}x faster")
            
            if speedup > 2:
                print("\n✓ PASS: Cache providing significant speedup")
            else:
                print("\n⚠ WARNING: Cache speedup less than expected")
    
    def test_stress(self, duration_seconds=60):
        """Test 6: Sustained load stress test"""
        print("\n" + "="*60)
        print(f"TEST 6: Stress Test ({duration_seconds} seconds)")
        print("="*60)
        
        start_time = time.time()
        request_count = 0
        errors = 0
        
        while time.time() - start_time < duration_seconds:
            try:
                response = requests.get(
                    f"{self.api_base_url}/api/v1/recommendations/user/1",
                    params={'n': 10},
                    timeout=10
                )
                request_count += 1
                if response.status_code != 200:
                    errors += 1
            except:
                errors += 1
            
            # Brief pause to avoid overwhelming
            time.sleep(0.1)
        
        actual_duration = time.time() - start_time
        throughput = request_count / actual_duration
        error_rate = (errors / request_count * 100) if request_count > 0 else 0
        
        print(f"\n📊 Stress Test Results:")
        print(f"  Duration:          {actual_duration:.2f} seconds")
        print(f"  Total Requests:    {request_count}")
        print(f"  Errors:            {errors}")
        print(f"  Error Rate:        {error_rate:.2f}%")
        print(f"  Throughput:        {throughput:.2f} req/sec")
        
        if error_rate < 1:
            print("\n✓ PASS: Error rate < 1%")
        else:
            print("\n✗ FAIL: Error rate too high")
    
    def run_full_test_suite(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("RECOMMENDATION API - FULL TEST SUITE")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # Test 1: Health Check
        health_ok = self.test_health_check()
        if not health_ok:
            print("\n❌ API is not healthy. Stopping tests.")
            return
        
        # Test 2: Response Time
        self.test_response_time('/api/v1/recommendations/user/1', {'n': 10})
        
        # Test 3: Concurrent Load
        self.test_concurrent_requests('/api/v1/recommendations/user/1')
        
        # Test 4: All Endpoints
        self.test_different_endpoints()
        
        # Test 5: Cache
        self.test_cache_effectiveness('/api/v1/recommendations/user/1?n=10')
        
        # Test 6: Stress Test
        self.test_stress(duration_seconds=30)
        
        print("\n" + "="*60)
        print("TEST SUITE COMPLETED")
        print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)


# ============================================
# LOAD TESTING WITH LOCUST (Alternative)
# ============================================

"""
Save this as locustfile.py and run: locust -f locustfile.py

from locust import HttpUser, task, between

class RecommendationUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    @task(3)  # Weight: 3
    def get_user_recommendations(self):
        user_id = random.randint(1, 1000)
        self.client.get(f"/api/v1/recommendations/user/{user_id}?n=10")
    
    @task(2)  # Weight: 2
    def get_similar_items(self):
        item_id = random.randint(1, 500)
        self.client.get(f"/api/v1/recommendations/similar/{item_id}?n=10")
    
    @task(1)  # Weight: 1
    def get_popular_items(self):
        self.client.get("/api/v1/recommendations/popular?n=10")

# Run with: locust -f locustfile.py --host=http://localhost:5000
"""


if __name__ == "__main__":
    """
    Run the test suite
    """
    # Update this to your API URL
    API_URL = "http://localhost:5000"
    
    print("\nRecommendation API Performance Testing")
    print("=======================================")
    
    tester = RecommendationAPITester(api_base_url=API_URL)
    
    # Run full test suite
    tester.run_full_test_suite()
    
    print("\n✓ All tests completed!")
    print("\nReview the results above to ensure:")
    print("  1. Response time < 200ms (95th percentile)")
    print("  2. Success rate >= 99.5%")
    print("  3. Cache is working effectively")
    print("  4. System handles concurrent load well")
