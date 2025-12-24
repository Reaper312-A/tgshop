import logging
from payment.cryptobot import CryptoBotPayment
from config import CRYPTOBOT_API_TOKEN

# Включаем детальное логирование
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_payment():
    """Тестирование платежной системы с улучшенной обработкой ошибок"""
    print("🧪 Тестирование CryptoBot интеграции v2...")
    print("=" * 50)
    
    try:
        # Инициализация
        print("1. Инициализация CryptoBot...")
        cryptobot = CryptoBotPayment(CRYPTOBOT_API_TOKEN, test_mode=False)
        
        # 2. Проверка подключения
        print("\n2. Проверка подключения к API...")
        try:
            me = cryptobot.get_me()
            print(f"   ✅ Подключение успешно!")
            print(f"   👤 Имя бота: {me.get('name', 'N/A')}")
            print(f"   🆔 App ID: {me.get('app_id', 'N/A')}")
            print(f"   🌐 Payment URL: {me.get('payment_processing_bot_username', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Ошибка подключения: {e}")
            return
        
        # 3. Проверка баланса
        print("\n3. Проверка баланса...")
        try:
            balance = cryptobot.get_balance()
            if balance:
                print(f"   ✅ Получено {len(balance)} активов:")
                for asset in balance:
                    asset_code = asset.get('asset_code', 'N/A')
                    available = asset.get('available', '0')
                    print(f"      💰 {asset_code}: {available}")
            else:
                print("   ℹ️ Баланс пуст или недоступен")
        except Exception as e:
            print(f"   ⚠️ Ошибка получения баланса: {e}")
        
        # 4. Проверка поддерживаемых активов
        print("\n4. Проверка поддерживаемых активов...")
        try:
            assets = cryptobot.get_supported_assets()
            print(f"   ✅ Поддерживаемые активы: {', '.join(assets[:10])}")
            if len(assets) > 10:
                print(f"      ... и еще {len(assets) - 10} активов")
        except Exception as e:
            print(f"   ⚠️ Ошибка получения активов: {e}")
        
        # 5. Тестирование создания счета
        print("\n5. Тестирование создания счета...")
        try:
            # Создаем тестовый счет на 10 рублей (минимальная сумма)
            test_invoice = cryptobot.create_invoice(
                amount=10,
                currency="RUB",
                asset="USDT",
                description="Тестовый счет для проверки",
                hidden_message="Тест успешен!",
                paid_btn_name="callback",
                paid_btn_url="https://t.me/your_bot",
                expires_in=600  # 10 минут
            )
            
            print(f"   ✅ Счет успешно создан!")
            print(f"   🆔 Invoice ID: {test_invoice.get('invoice_id')}")
            print(f"   🔗 Pay URL: {test_invoice.get('pay_url')}")
            print(f"   💰 Сумма: {test_invoice.get('amount')} {test_invoice.get('asset')}")
            print(f"   📝 Описание: {test_invoice.get('description')}")
            print(f"   ⏰ Статус: {test_invoice.get('status')}")
            print(f"   🕒 Действует до: {test_invoice.get('expiration_date')}")
            
            # Сохраняем ID для проверки статуса
            invoice_id = test_invoice.get('invoice_id')
            
            # 6. Проверка статуса счета
            print("\n6. Проверка статуса счета...")
            status = cryptobot.check_invoice_status(invoice_id)
            print(f"   📊 Статус счета: {status}")
            
        except Exception as e:
            print(f"   ❌ Ошибка создания счета: {e}")
            print("\n   🔧 Возможные причины:")
            print("   1. Недостаточно средств на балансе бота")
            print("   2. Неправильный формат запроса")
            print("   3. Ограничения CryptoBot API")
            return
        
        # 7. Проверка курсов
        print("\n7. Проверка курсов обмена...")
        try:
            rates = cryptobot.get_exchange_rates()
            if rates:
                print(f"   ✅ Получено {len(rates)} курсов")
                # Показываем несколько актуальных курсов
                usdt_rate = next((r for r in rates if r.get('source') == 'USDT' and r.get('target') == 'RUB'), None)
                if usdt_rate:
                    print(f"   💱 USDT/RUB: {usdt_rate.get('rate')}")
            else:
                print("   ℹ️ Курсы не получены")
        except Exception as e:
            print(f"   ⚠️ Ошибка получения курсов: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Тестирование завершено!")
        print("\n📋 Рекомендации:")
        print("1. Проверьте баланс в @CryptoBot")
        print("2. Пополните баланс USDT для приема платежей")
        print("3. Протестируйте полный цикл оплаты")
        
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        print("\n🔧 Проверьте:")
        print("1. Правильность API токена в config.py")
        print("2. Доступность https://pay.crypt.bot")
        print("3. Настройки CryptoBot (@CryptoBot -> Crypto Pay -> API)")
        print("4. Баланс бота для создания счетов")

if __name__ == "__main__":
    test_payment()