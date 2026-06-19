select 
	specialization, 
	COUNT(*) AS doctor_count 
FROM harmonized.doctors 
GROUP BY specialization;

select 
	a.status, 
	count(a.status) 
from harmonized.appointments a
group by status;

select 
	p.insurance_provider,
	count(p.insurance_provider)
from harmonized.patients p
group by insurance_provider;

select 
	t.treatment_type, 
	sum(b.amount) as total  
from harmonized.treatments t
join harmonized.billing b on t.treatment_id  = b.treatment_id 
group by t.treatment_type;