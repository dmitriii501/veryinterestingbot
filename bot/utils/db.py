from supabase import create_client, Client
from bot.config import SUPABASE_URL, SUPABASE_KEY

# Создаем клиент Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)