from flask import Flask, jsonify, request
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.ads.google_ads.client import GoogleAdsClient
from google.ads.google_ads.errors import GoogleAdsException
from marshmallow import Schema, fields, validate
from models import UserAccess, UserAccessInvitation, db

# pip install Flask
# pip install google-auth
# pip install google-ads
# pip install marshmallow



app = Flask(__name__)

# Set up Google Ads API client
credentials = Credentials.from_authorized_user_file('google_ads_auth.json')
client = GoogleAdsClient(credentials=credentials)


# Define endpoints for managing user access and user access invitations

class UserAccessSchema(Schema):
    user_id = fields.Integer(required=True)
    email_address = fields.Email(required=True)
    access_role = fields.String(
        required=True,
        validate=validate.OneOf(
            ['ADMIN', 'STANDARD', 'READ_ONLY', 'EMAIL_ONLY']
        )
    )

class UserAccessInvitationSchema(Schema):
    email_address = fields.Email(required=True)
    access_role = fields.String(
        required=True,
        validate=validate.OneOf(
            ['ADMIN', 'STANDARD', 'READ_ONLY', 'EMAIL_ONLY']
        )
    )


# Define endpoints for managing user access and user access invitations
@app.route('/api/user_access', methods=['GET'])
def get_user_access():
    try:
        # Query the UserListAccess resource to get all user access information
        query = f"SELECT customer_user_access.user_id, customer_user_access.email_address, customer_user_access.access_role, customer_user_access.inviter_user_email FROM customer_user_access"
        response = client.service.google_ads_service.search(query=query)

        # Process the response and return user access information as JSON
        user_access_list = []
        for row in response:
            user_access = {}
            for field in row.customer_user_access:
                user_access[field] = getattr(row.customer_user_access, field)
            user_access_list.append(user_access)
        return jsonify(user_access_list), 200
    except GoogleAdsException as ex:
        error_list = []
        for error in ex.errors:
            error_list.append(error.error_string)
        return jsonify(error_list), 400

@app.route('/api/user_access', methods=['POST'])
def create_user_access():
    try:
        # Parse request JSON and validate required fields
        request_data = request.get_json()
        user_id = request_data['user_id']
        email_address = request_data['email_address']
        access_role = request_data['access_role']

        # Create the UserListAccess resource with the provided information
        user_access = client.resource('CustomerUserAccess')
        user_access.email_address = email_address
        user_access.access_role = access_role
        user_access.user_id = user_id

        # Issue a mutate operation to create the UserListAccess resource
        mutate_operation = client.service.customer_user_access_service.mutate_customer_user_accesses(
            customer_id=client.config.client_customer_id,
            operations=[{'create': user_access}]
        )
        response = mutate_operation.result()

        # Return success status and created user access information as JSON
        user_access_list = []
        for result in response.results:
            created_user_access = {}
            for field in result.customer_user_access:
                created_user_access[field] = getattr(result.customer_user_access, field)
            user_access_list.append(created_user_access)
        return jsonify(user_access_list), 201
    except GoogleAdsException as ex:
        error_list = []
        for error in ex.errors:
            error_list.append(error.error_string)
        return jsonify(error_list), 400

@app.route('/api/user_access/<user_id>', methods=['DELETE'])
def delete_user_access(user_id):
    try:
        # Issue a mutate operation to delete the UserListAccess resource with the provided user ID
        mutate_operation = client.service.customer_user_access_service.mutate_customer_user_accesses(
            customer_id=client.config.client_customer_id,
            operations=[{'remove': user_id}]
        )
        mutate_operation.result()

        # Return success status
        return jsonify({'message': f'User access with user ID {user_id} has been deleted'}), 200
    except GoogleAdsException as ex:
        error_list = []
        for error in ex.errors:
            error_list.append(error.error_string)
        return jsonify(error_list), 400

@app.route('/api/user_access_invitations', methods=['GET'])
def get_user_access_invitations():
    try:
        # Get all user access invitations from the database
        user_access_invitations = UserAccessInvitation.query.all()

        # Serialize the user access invitations data
        user_access_invitations_schema = UserAccessInvitationSchema(many=True)
        data = user_access_invitations_schema.dump(user_access_invitations)

        # Return success response
        return jsonify({
            "status": "success",
            "data": data
        }), 200
    except Exception as e:
        # Return error response
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/user_access_invitations', methods=['POST'])
def create_user_access_invitation():
    try:
        # Parse request data
        request_data = request.get_json()
        email = request_data.get('email')
        account_id = request_data.get('account_id')

        # Validate input data
        if not email or not account_id:
            raise ValueError("Email and account ID are required.")

        # Check if the user already has access to the account
        user_access = UserAccess.query.filter_by(email=email, account_id=account_id).first()
        if user_access:
            raise ValueError("The user already has access to the account.")

        # Check if the user access invitation already exists
        user_access_invitation = UserAccessInvitation.query.filter_by(email=email, account_id=account_id).first()
        if user_access_invitation:
            raise ValueError("A user access invitation already exists for this user and account.")

        # Create the user access invitation
        user_access_invitation = UserAccessInvitation(
            email=email,
            account_id=account_id
        )
        db.session.add(user_access_invitation)
        db.session.commit()

        # Serialize the user access invitation data
        user_access_invitation_schema = UserAccessInvitationSchema()
        data = user_access_invitation_schema.dump(user_access_invitation)

        # Return success response
        return jsonify({
            "status": "success",
            "message": "User access invitation has been created",
            "data": data
        }), 201
    except ValueError as e:
        # Return error response
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    except Exception as e:
        # Return error response
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500



@app.route('/api/user_access_invitations/<int:user_access_invitation_id>', methods=['DELETE'])
def delete_user_access_invitation(user_access_invitation_id):
    try:
        # Get the user access invitation to be deleted
        user_access_invitation = UserAccessInvitation.query.get(user_access_invitation_id)

        # Check if the user access invitation exists
        if not user_access_invitation:
            raise ValueError("User access invitation not found.")

        # Delete the user access invitation
        db.session.delete(user_access_invitation)
        db.session.commit()

        # Return success response
        return jsonify({
            "status": "success",
            "message": "User access invitation deleted successfully."
        }), 200
    except Exception as e:
        # Return error response
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

