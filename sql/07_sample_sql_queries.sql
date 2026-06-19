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

select
p.first_name || ' ' ||  p.last_name as patient_name,
sum(amount) as total_bill
from harmonized.billing b
join harmonized.patients p on p.patient_id = b.patient_id
group by p.patient_id, patient_name
order by total_bill desc
limit 1;
