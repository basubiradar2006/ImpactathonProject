from supabase import create_client

url = "https://dckzggsaoecqohcjmkho.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRja3pnZ3Nhb2VjcW9oY2pta2hvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg5Mjc2NzMsImV4cCI6MjA5NDUwMzY3M30.DFH9IQRY_2Dv4sSo5T2OGGwY-Soy2WjYHxIwTUXJ2pc"

supabase = create_client(url, key)

print("CONNECTED")