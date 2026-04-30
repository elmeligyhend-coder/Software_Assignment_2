package com.finance;
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        DatabaseManager.initialize();
        
        UserRepository userRepo = new UserRepository();
        Scanner sc = new Scanner(System.in);

        System.out.println("--- Welcome in Personal Budgeting Software ---");
        
        while (true) {
            System.out.println("\n1. Sign Up");
            System.out.println("2. Login");
            System.out.println("3. Exit");
            System.out.print("Select action: ");
            
            int choice = sc.nextInt();
            sc.nextLine(); 

            if (choice == 1) {
                System.out.println("\nSIGN UP");
                System.out.print("Enter Name: ");
                String name = sc.nextLine();
                System.out.print("Enter Email: ");
                String email = sc.nextLine();
                System.out.print("Enter Password: ");
                String pass = sc.nextLine();

                if (userRepo.signUp(name, email, pass)) {
                    System.out.println(">>> Account created successfully and saved in Database!");
                } else {
                    System.out.println(">>> Error: Email already exists in our records.");
                }

            } else if (choice == 2) {
                System.out.println("\nLOGIN");
                boolean loginSuccess = false;

                while (!loginSuccess) {
                    System.out.print("Enter Email: ");
                    String email = sc.nextLine();
                    System.out.print("Enter Password: ");
                    String pass = sc.nextLine();

                    int userId = userRepo.login(email, pass);

                    if (userId != -1) {
                        System.out.println(">>> Login Successful! Welcome ID: " + userId);
                        loginSuccess = true; 
                        System.out.println("Returning to Main Menu...");
                    } else {
                        System.out.println(">>> [X] Invalid Email or Password! Please try again.");
                        System.out.println("-------------------------------------------------");
                    }
                }
            } else if (choice == 3) {
                System.out.println("Closing System...");
                break;
            }
        }
        sc.close();
    }
}