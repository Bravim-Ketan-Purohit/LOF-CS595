import csv
import json
import sys
import os

import requests
from fhirclient import client
from fhirclient.models.codeableconcept import CodeableConcept
from fhirclient.models.coding import Coding
from fhirclient.models.condition import Condition
from fhirclient.models.extension import Extension
from fhirclient.models.fhirdatetime import FHIRDateTime
from fhirclient.models.fhirreference import FHIRReference

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), './../..')))
from labs.ccd.services.ccd_services import CCDServices
from lof.services import HealthGorillaTokenService

BASE_URL = "https://sandbox.healthgorilla.com/fhir"

# FHIR server settings
settings = {
    "app_id": "CCD",
    "api_base": "http://localhost:8080/fhir"
}
# Initialize FHIR client
smart = client.FHIRClient(settings=settings)


class HealthGorillaETLPipeline():

    def __init__(self):
        self.ccd_service = CCDServices()

    def csv_to_dictionary(self):
        patientDict = {}
        inc = 0
        with open('patients.csv') as infile:
            for line in csv.DictReader(infile):
                patientDict[inc] = line
                inc += 1
        return patientDict

    def retrieve_patient_from_hg(self, patient):
        """
        TODO: Instructions for implementing this function:
        
        1. Extract patient information from input dictionary:
           - Get first name from patient['First Name']
           - Get last name from patient['Last Name'] 
           - Split DOB string from patient['DOB'] into month, day, year using '/' delimiter
        
        2. Format birth date into YYYY-MM-DD format:
           - Pad month and day with leading zeros if needed
           - Combine year, month, day with '-' separator
        
        3. Construct Health Gorilla API URL:
           - Use BASE_URL constant
           - Add /Patient endpoint
           - Add query parameters for:
             * given (first name)
             * family (last name) 
             * birthdate
        
        4. Set up request headers:
           - Get bearer token from HealthGorillaTokenService
           - Set Content-Type to application/json
        
        5. Make GET request to Health Gorilla API:
           - Use requests library
           - Pass URL and headers
           - Parse JSON response
        
        6. Handle response based on number of matches:
           - If total = 0: return empty dict (no matches)
           - If total = 1: return first entry (exact match)
           - If total > 1: return first entry (multiple matches)
           - Print appropriate message for each case
        """


    def transform_hg_to_ccd(self, hg_data):
        """
        TODO: Instructions for implementing this function:

        1. Extract resource data from hg_data input
        
        2. Get MRN/EHR code:
           - Loop through resource['identifier'] array
           - Find identifier where type.coding[0].code = 'MR'
           - Set ehr_code to identifier.value
        
        3. Extract name components:
           - Get first_name from resource.name[0].given[0]
           - Get last_name from resource.name[0].family
        
        4. Create username and email:
           - Username = lowercase(first_name + last_name)
           - Email = username@example.com
        
        5. Get address details:
           - Extract address components from resource.address[0]
           - Combine line[0], city, state, postalCode into full_address
        
        6. Format birthdate:
           - Add time component to resource.birthDate
           - Format as YYYY-MM-DDT00:00:00Z
        
        7. Construct and return JSON object with:
           - username, email from step 4
           - first_name, last_name from step 3
           - dummy passwords
           - dob from step 6
           - gender from resource
           - ehr_code from step 2
           - user_profile with:
             * address from step 5
             * dummy phone
             * email alert preferences
        """

        ao_json = {
            "username": "",
            "email": "",
            "first_name": "",
            "last_name": "",
            "password1": "Password123!",  # Dummy password
            "password2": "Password123!",  # Dummy password
            "dob": "",
            "gender": "",
            "ehr_code": "",
            "user_profile": {
                "address": "",
                "phone": "1234567890",  # Dummy phone number
                "preferred_alert_mode": "Email",
                "secondary_alert_mode": "Email"
            }
        }

        return ao_json

    def create_patients(self):
        patient_list = self.csv_to_dictionary()
        # loop through each patient in the patient list
        patients_json = {}
        for patient in patient_list:
            # Retrieve patient details from HealthGorilla
            patient_details = self.retrieve_patient_from_hg(patient_list[patient])
            ccd_patient_json = self.transform_hg_to_ccd(patient_details)
            ccd_patient_json['mrn'] = ''
            ccd_patient = self.ccd_service.register_patient(ccd_patient_json)
            patients_json[patient_details['resource']['id']] = ccd_patient_json

        with open('patients.json', 'w') as pf:
            json.dump(patients_json, pf, indent=4)

    def retrieve_conditions_from_hg(self, hg_patient_id):
        """
        TODO: Instructions for implementing this function:
        
        1. Set up the API endpoint by combining BASE_URL with "/Condition"
        
        2. Create a params dictionary with:
           - "patient": hg_patient_id to filter conditions by patient
        
        3. Set up request headers:
           - Add "Authorization" header with Bearer token from self.get_bearer_token()
           - Add "Content-Type" header as "application/json"
        
        4. Make GET request to Health Gorilla API:
           - Use requests.get() with endpoint, headers and params
           - Handle the response:
             - Check status code with raise_for_status()
             - Parse JSON response
             - Return condition data
        
        5. Add error handling:
           - Catch HTTPError exceptions and return error dict
           - Catch general exceptions and return error dict
        
        Parameters:
            hg_patient_id (str): Health Gorilla patient ID to get conditions for
            
        Returns:
            dict: JSON response with conditions data or error message
        """


    def get_codeable_concept(self, system, code, display):
        codeable_concept = CodeableConcept()
        codings = []
        coding = Coding()
        coding.system = system
        coding.code = code
        coding.display = display
        codings.append(coding)
        codeable_concept.coding = codings
        return codeable_concept

    def get_codes(self, resource):
        code = CodeableConcept()
        codings = []
        for coding_data in resource['code']['coding']:
            coding = Coding()
            coding.system = coding_data.get('system')
            coding.code = coding_data.get('code')
            coding.display = coding_data.get('display')
            code.text = coding.display
            codings.append(coding)
        code.coding = codings
        return code

    def create_ccd_condition(self, hg_condition, mrn):
        """
        TODO: Instructions for implementing this function:
        
        1. Extract resource data from hg_condition parameter:
           - Get 'resource' field from hg_condition dict, default to empty dict if not present
        
        2. Set clinical and verification status:
           - Set condition.clinicalStatus to Active using get_codeable_concept()
                - system: http://terminology.hl7.org/CodeSystem/condition-clinical
           - Set condition.verificationStatus to Confirmed using get_codeable_concept()
                - system: http://terminology.hl7.org/CodeSystem/condition-ver-status
        
        3. Handle extensions if present:
           - Check if 'extension' exists in resource
           - For each extension:
             - Create Extension object
             - Set URL from extension data
             - If valueReference exists, create FHIRReference and set reference
             - Add to extensions list
           - Set condition.extension
        
        4. Set condition category:
           - Create category for 'problem-list-item' using get_codeable_concept()
                - system: http://terminology.hl7.org/CodeSystem/condition-category
           - Add to categories list
           - Set condition.category
        
        5. Set condition code if present:
           - Check if 'code' exists in resource
           - Use get_codes() to set condition.code
        
        6. Set subject reference:
           - Check if 'subject' exists in resource
           - Create FHIRReference with patient MRN
           - Set display from resource subject
           - Set condition.subject
        
        7. Set dates if present:
           - Set onsetDateTime if exists
           - Set assertedDate if exists
        
        8. Create condition in FHIR server:
           - Use condition.create() to post to server
           - Return response
        """
        condition = Condition()

        # Post the Condition resource to the FHIR server
        response = condition.create(smart.server)
        return response


    def create_condition(self, hg_patient_id, mrn):
        hg_conditions = self.retrieve_conditions_from_hg(hg_patient_id)
        for hg_condition in hg_conditions['entry']:
            try:
                self.create_ccd_condition(hg_condition, mrn)
            except Exception as e:
                print('Error while adding condition ' + repr(e))


    def delete_patient_from_ccd(self, mrn):
        self.ccd_service.delete_patient(patient_id=mrn)


if __name__ == '__main__':
    hg_etl_pipeline = HealthGorillaETLPipeline()

    # Step 1: Create Patients
    # hg_etl_pipeline.create_patients()

    # Step 2: Open patients.json and Update MRN

    # Step 3 : Populate Conditions
    # with open('patients.json', 'r') as pf:
    #     patients_json = json.load(pf)
    #
    # for patient in patients_json:
    #     condition_response = hg_etl_pipeline.create_condition(hg_patient_id=patient,
    #                                                           mrn=patients_json[patient]['mrn'])

    # Delete the patient by MRN
    # hg_etl_pipeline.delete_patient_from_ccd(mrn='2361')
    # hg_etl_pipeline.delete_patient_from_ccd(mrn='2362')
