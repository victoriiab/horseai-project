"""
Тесты для проверки URL endpoints
"""
from django.test import SimpleTestCase
from django.urls import reverse, resolve
from frontend import views

class TestUrls(SimpleTestCase):
    """Тестирование основных URL"""
    
    def test_index_url(self):
        """Тест главной страницы"""
        url = reverse('index')
        print(f"Testing URL: {url}")
        try:
            resolved = resolve(url)
            print(f"Resolved to: {resolved.func}")
            self.assertEqual(resolved.func, views.index)
        except Exception as e:
            print(f"Error resolving URL: {e}")
            raise
    
    def test_login_url(self):
        """Тест страницы входа"""
        url = reverse('login')
        print(f"Testing URL: {url}")
        try:
            resolved = resolve(url)
            print(f"Resolved to: {resolved.func}")
            self.assertEqual(resolved.func, views.custom_login)
        except Exception as e:
            print(f"Error resolving URL: {e}")
            raise
    
    def test_video_upload_url(self):
        """Тест загрузки видео"""
        url = reverse('video_upload')
        print(f"Testing URL: {url}")
        try:
            resolved = resolve(url)
            print(f"Resolved to: {resolved.func}")
            self.assertEqual(resolved.func, views.video_upload)
        except Exception as e:
            print(f"Error resolving URL: {e}")
            raise
    
    def test_analysis_results_url(self):
        """Тест результатов анализа"""
        url = reverse('analysis_results')
        print(f"Testing URL: {url}")
        try:
            resolved = resolve(url)
            print(f"Resolved to: {resolved.func}")
            self.assertEqual(resolved.func, views.analysis_results)
        except Exception as e:
            print(f"Error resolving URL: {e}")
            raise

class TestApiUrls(SimpleTestCase):
    """Тестирование API URLs"""
    
    def test_api_upload_simple_real(self):
        """Тест API загрузки видео"""
        url = reverse('api_upload_simple_real')
        print(f"Testing API URL: {url}")
        try:
            resolved = resolve(url)
            print(f"Resolved to: {resolved.func}")
            self.assertEqual(resolved.func, views.upload_video_simple_api_real)
        except Exception as e:
            print(f"Error resolving URL: {e}")
            raise
    
    def test_api_system_stats(self):
        """Тест API статистики"""
        url = reverse('system_stats')
        print(f"Testing API URL: {url}")
        try:
            resolved = resolve(url)
            print(f"Resolved to: {resolved.func}")
            self.assertEqual(resolved.func, views.get_system_stats)
        except Exception as e:
            print(f"Error resolving URL: {e}")
            raise

def run_all_tests():
    """Запуск всех тестов"""
    import sys
    from django.test.runner import DiscoverRunner
    
    test_runner = DiscoverRunner()
    failures = test_runner.run_tests(['frontend.tests'])
    
    if failures:
        sys.exit(1)
    else:
        print("✅ Все тесты прошли успешно!")
        sys.exit(0)

if __name__ == '__main__':
    run_all_tests()
