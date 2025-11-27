import csv
import os
import random

# ========================================
# 📊 Data Generation Settings (Adjust node counts here)
# ========================================
NUM_COMPANIES = 20      # Number of companies to generate
NUM_TECHNOLOGIES = 100  # Number of technologies to generate
NUM_RELATIONS = 300     # Number of relations to generate

# Base Data
base_companies = [
    {'name': 'LG Energy Solution', 'country': 'Korea'},
    {'name': 'Tesla', 'country': 'USA'},
    {'name': 'CATL', 'country': 'China'},
    {'name': 'SK On', 'country': 'Korea'},
    {'name': 'Samsung SDI', 'country': 'Korea'},
    {'name': 'Panasonic', 'country': 'Japan'},
    {'name': 'BYD', 'country': 'China'},
    {'name': 'Northvolt', 'country': 'Sweden'},
    {'name': 'QuantumScape', 'country': 'USA'},
    {'name': 'Solid Power', 'country': 'USA'},
    {'name': 'StoreDot', 'country': 'Israel'},
    {'name': 'CALB', 'country': 'China'},
    {'name': 'Guoxuan High-Tech', 'country': 'China'},
    {'name': 'EVE Energy', 'country': 'China'},
    {'name': 'Sunwoda', 'country': 'China'},
    {'name': 'Farasis Energy', 'country': 'China'},
    {'name': 'AESC', 'country': 'Japan'},
    {'name': 'Verkor', 'country': 'France'},
    {'name': 'Morrow Batteries', 'country': 'Norway'},
    {'name': 'Freyr', 'country': 'Norway'},
    {'name': 'Rivian', 'country': 'USA'},
    {'name': 'Volkswagen', 'country': 'Germany'},
    {'name': 'Toyota', 'country': 'Japan'},
    {'name': 'General Motors', 'country': 'USA'},
    {'name': 'Ford', 'country': 'USA'}
]

base_technologies = [
    {'name': 'NCM Battery', 'category': 'Battery'},
    {'name': 'LFP Battery', 'category': 'Battery'},
    {'name': 'BMS', 'category': 'Software'},
    {'name': 'NCA Battery', 'category': 'Battery'},
    {'name': 'Solid-State Battery', 'category': 'Battery'},
    {'name': 'Silicon Anode', 'category': 'Material'},
    {'name': 'Sodium-Ion Battery', 'category': 'Battery'},
    {'name': 'Li-Metal Battery', 'category': 'Battery'},
    {'name': 'Thermal Management System', 'category': 'Hardware'},
    {'name': 'Battery Recycling', 'category': 'Service'},
    {'name': '4680 Cell', 'category': 'Form Factor'},
    {'name': 'Blade Battery', 'category': 'Form Factor'},
    {'name': 'Cylindrical Cell', 'category': 'Form Factor'},
    {'name': 'Prismatic Cell', 'category': 'Form Factor'},
    {'name': 'Pouch Cell', 'category': 'Form Factor'}
]

base_relations = [
    ('LG Energy Solution', 'NCM Battery'),
    ('LG Energy Solution', 'NCA Battery'),
    ('LG Energy Solution', 'BMS'),
    ('Tesla', 'LFP Battery'),
    ('Tesla', 'NCA Battery'),
    ('CATL', 'LFP Battery'),
    ('CATL', 'NCM Battery'),
    ('SK On', 'NCM Battery'),
    ('Samsung SDI', 'NCA Battery'),
    ('Panasonic', 'NCA Battery'),
    ('BYD', 'LFP Battery'),
    ('Northvolt', 'NCM Battery'),
    ('QuantumScape', 'Solid-State Battery'),
]

# Synthetic Data Generators
company_prefixes = ['Global', 'Eco', 'Future', 'Advanced', 'Green', 'Smart', 'Ultra', 'Mega', 'Hyper', 'Next', 'Pure', 'Volt', 'Amp', 'Ion', 'Power']
company_suffixes = ['Energy', 'Power', 'Systems', 'Tech', 'Solutions', 'Batteries', 'Storage', 'Dynamics', 'Innovations', 'Labs', 'Group', 'Corp', 'Inc', 'Ltd', 'Holdings']
countries = ['Korea', 'USA', 'China', 'Japan', 'Germany', 'France', 'Sweden', 'Norway', 'UK', 'Canada', 'Australia', 'India']

tech_prefixes = ['High-Capacity', 'Fast-Charging', 'Long-Life', 'Ultra-Safe', 'Eco-Friendly', 'Advanced', 'NextGen', 'Smart', 'Hybrid', 'Composite', 'Nano', 'Quantum']
tech_bases = ['Anode', 'Cathode', 'Electrolyte', 'Separator', 'Cell', 'Module', 'Pack', 'BMS', 'Sensor', 'Inverter', 'Converter', 'Charger']
tech_suffixes = ['v1', 'v2', 'Pro', 'Max', 'Plus', 'Ultra', 'X', 'Y', 'Z', 'Alpha', 'Beta', 'Gamma']
categories = ['Battery', 'Software', 'Material', 'Hardware', 'Service', 'Form Factor']

def generate_companies(target_count=10000):
    generated = base_companies.copy()
    existing_names = set(c['name'] for c in generated)
    
    while len(generated) < target_count:
        name = f"{random.choice(company_prefixes)} {random.choice(company_suffixes)} {random.randint(1, 9999)}"
        if name not in existing_names:
            country = random.choice(countries)
            generated.append({'name': name, 'country': country})
            existing_names.add(name)
    return generated

def generate_technologies(target_count=100000):
    generated = base_technologies.copy()
    existing_names = set(t['name'] for t in generated)
    
    while len(generated) < target_count:
        name = f"{random.choice(tech_prefixes)} {random.choice(tech_bases)} {random.choice(tech_suffixes)} {random.randint(1, 9999)}"
        if name not in existing_names:
            category = random.choice(categories)
            generated.append({'name': name, 'category': category})
            existing_names.add(name)
    return generated

def generate_relations(companies, technologies, target_count=10000):
    generated = set(base_relations)
    
    # Ensure connectivity: every company has at least one tech
    for company in companies:
        tech = random.choice(technologies)
        generated.add((company['name'], tech['name']))
        
    # Ensure connectivity: every tech has at least one company
    for tech in technologies:
        company = random.choice(companies)
        generated.add((company['name'], tech['name']))
        
    # Fill up to target count
    while len(generated) < target_count:
        company = random.choice(companies)
        tech = random.choice(technologies)
        generated.add((company['name'], tech['name']))
        
    return list(generated)

def write_csv(filename, headers, data):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

def write_relations_csv(filename, headers, data):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(data)

if __name__ == "__main__":
    base_path = "/Users/donghakim/python_workspace/251125_FalkorDB/data/csv"
    
    print("=" * 60)
    print("FalkorDB Data Generation")
    print("=" * 60)
    print(f"📊 Settings:")
    print(f"   - Companies: {NUM_COMPANIES}")
    print(f"   - Technologies: {NUM_TECHNOLOGIES}")
    print(f"   - Relations: {NUM_RELATIONS}")
    print("=" * 60)
    
    print("\n🏢 Generating companies...")
    companies = generate_companies(NUM_COMPANIES) 
    write_csv(os.path.join(base_path, 'companies.csv'), ['name', 'country'], companies)
    print(f"   ✅ {len(companies)} companies generated")

    print("\n🔋 Generating technologies...")
    technologies = generate_technologies(NUM_TECHNOLOGIES)
    write_csv(os.path.join(base_path, 'technologies.csv'), ['name', 'category'], technologies)
    print(f"   ✅ {len(technologies)} technologies generated")

    print("\n🔗 Generating relations...")
    relations = generate_relations(companies, technologies, NUM_RELATIONS)
    write_relations_csv(os.path.join(base_path, 'relations.csv'), ['company', 'technology'], relations)
    print(f"   ✅ {len(relations)} relations generated")
    
    print("\n" + "=" * 60)
    print("✅ Data generation complete!")
    print(f"📁 Save location: {base_path}")
    print("=" * 60)
