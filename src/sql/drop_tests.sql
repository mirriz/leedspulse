-- Delete all users created by Pytest
DELETE FROM public.users 
WHERE email LIKE 'pytest_%' OR email LIKE 'test_%';

