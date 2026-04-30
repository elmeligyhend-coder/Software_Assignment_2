package com.finance;

public class Transaction {
    private int id;
    private int userId;
    private double amount;
    private String category;
    private String date;

    public Transaction(int userId, double amount, String category, String date) {
        this.userId = userId;
        this.amount = amount;
        this.category = category;
        this.date = date;
    }
    public int getUserId() { return userId; }
    public double getAmount() { return amount; }
    public String getCategory() { return category; }
    public String getDate() { return date; }
}