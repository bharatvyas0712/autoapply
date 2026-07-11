"""
Unit tests for retry utilities.
"""

import unittest
import time
from retry_utils import retry_with_backoff, RetryError


class TestRetryUtils(unittest.TestCase):
    """Test cases for retry utilities."""
    
    def test_successful_operation_no_retry(self):
        """Test that successful operations don't retry."""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3, base_delay=0.1)
        def successful_operation():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_operation()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 1)
    
    def test_retry_on_failure(self):
        """Test that failed operations retry."""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3, base_delay=0.1)
        def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"
        
        result = failing_operation()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 2)
    
    def test_max_attempts_exceeded(self):
        """Test that operation fails after max attempts."""
        @retry_with_backoff(max_attempts=2, base_delay=0.1)
        def always_failing_operation():
            raise ValueError("Always fails")
        
        with self.assertRaises(RetryError):
            always_failing_operation()
    
    def test_specific_exception_retry(self):
        """Test that only specified exceptions trigger retry."""
        call_count = 0
        
        @retry_with_backoff(
            max_attempts=3,
            base_delay=0.1,
            retryable_exceptions=(ValueError,)
        )
        def operation_with_different_exceptions():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Retry this")
            if call_count == 2:
                raise TypeError("Don't retry this")
            return "success"
        
        with self.assertRaises(TypeError):
            operation_with_different_exceptions()
        self.assertEqual(call_count, 2)


if __name__ == '__main__':
    unittest.main()
