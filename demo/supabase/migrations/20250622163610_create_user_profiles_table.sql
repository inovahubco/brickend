-- Create user_profiles table
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    username VARCHAR(50) UNIQUE NOT NULL,
    
    -- Datos demográficos
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    date_of_birth DATE,
    gender VARCHAR(20),
    phone VARCHAR(20),
    
    -- Ubicación
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'Colombia',
    
    -- Preferencias (JSON para flexibilidad)
    preferences JSONB DEFAULT '{}',
    
    -- Campos adicionales
    bio TEXT,
    avatar_url VARCHAR(500),
    website VARCHAR(500),
    occupation VARCHAR(100),
    
    -- Configuración de privacidad
    is_profile_public BOOLEAN DEFAULT false,
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps automáticos
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear índices para mejorar rendimiento
CREATE INDEX idx_user_profiles_user_id ON public.user_profiles(user_id) WHERE is_deleted = false;
CREATE INDEX idx_user_profiles_username ON public.user_profiles(username) WHERE is_deleted = false;
CREATE INDEX idx_user_profiles_created_at ON public.user_profiles(created_at) WHERE is_deleted = false;
CREATE INDEX idx_user_profiles_is_deleted ON public.user_profiles(is_deleted);

-- Crear función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Crear trigger para updated_at
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Crear función para soft delete
CREATE OR REPLACE FUNCTION soft_delete_user_profile()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_deleted = true AND OLD.is_deleted = false THEN
        NEW.deleted_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Crear trigger para soft delete
CREATE TRIGGER update_user_profiles_deleted_at
    BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION soft_delete_user_profile();

-- Habilitar RLS (Row Level Security)
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Política para que los usuarios solo puedan ver sus propios perfiles
CREATE POLICY "Users can view own profile" ON public.user_profiles
    FOR SELECT USING (auth.uid() = user_id);

-- Política para que los usuarios puedan insertar su propio perfil
CREATE POLICY "Users can insert own profile" ON public.user_profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Política para que los usuarios puedan actualizar su propio perfil
CREATE POLICY "Users can update own profile" ON public.user_profiles
    FOR UPDATE USING (auth.uid() = user_id);

-- Política para que los usuarios puedan hacer soft delete de su propio perfil
CREATE POLICY "Users can soft delete own profile" ON public.user_profiles
    FOR UPDATE USING (auth.uid() = user_id AND is_deleted = false);

-- Comentarios para documentación
COMMENT ON TABLE public.user_profiles IS 'Perfiles de usuarios complementarios a auth.users con información demográfica y preferencias';
COMMENT ON COLUMN public.user_profiles.user_id IS 'Referencia al usuario en auth.users';
COMMENT ON COLUMN public.user_profiles.username IS 'Nombre de usuario único';
COMMENT ON COLUMN public.user_profiles.preferences IS 'Preferencias del usuario en formato JSON';
COMMENT ON COLUMN public.user_profiles.is_deleted IS 'Indica si el perfil está eliminado lógicamente';
COMMENT ON COLUMN public.user_profiles.deleted_at IS 'Fecha y hora de eliminación lógica';
