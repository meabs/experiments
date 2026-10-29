package com.example.accounts.customer;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** A bank customer. {@code userId} is the customer's login (the token's {@code sub}). */
@Entity
@Table(name = "customers")
public class Customer {

    @Id
    private String id;

    @Column(nullable = false)
    private String tenantId;

    @Column(nullable = false, unique = true)
    private String userId;

    @Column(nullable = false)
    private String name;

    private String email;
    private String phone;
    private String address;

    /** Internal fraud and credit risk score, 0 to 100. Staff only: never shown to the customer. */
    private int riskScore;

    public String getId() { return id; }
    public String getTenantId() { return tenantId; }
    public String getUserId() { return userId; }
    public String getName() { return name; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public String getPhone() { return phone; }
    public void setPhone(String phone) { this.phone = phone; }
    public String getAddress() { return address; }
    public void setAddress(String address) { this.address = address; }
    public int getRiskScore() { return riskScore; }
}
